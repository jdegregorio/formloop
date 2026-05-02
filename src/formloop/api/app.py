"""FastAPI polling API for the Formloop harness.

REQ: FLH-F-025, FLH-D-019, FLH-D-022, FLH-NF-004, FLH-NF-006
"""

from __future__ import annotations

import asyncio
import mimetypes
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config.env import load_env_local
from ..config.profiles import HarnessConfig, load_config
from ..orchestrator import RunDriver
from ..orchestrator.run_driver import DriveRequest
from ..schemas import (
    ReferenceImageUploadResponse,
    ReviewSummary,
    RunCreateRequest,
    RunCreateResponse,
)
from ..store import RunStore

MAX_REFERENCE_IMAGE_BYTES = 10 * 1024 * 1024
REFERENCE_UPLOAD_DIR = Path("var/uploads/reference-images")


def create_app(config: HarnessConfig | None = None) -> FastAPI:
    """Build the FastAPI app — factory to support tests with a temp config."""

    load_env_local()
    cfg = config or load_config()
    store = RunStore(cfg.runs_dir)
    app = FastAPI(title="formloop", version="0.1.0")

    # Track background run tasks so the app doesn't exit before they finish
    # and so tests can await them deterministically.
    background: dict[str, asyncio.Task] = {}
    app.state.background = background
    app.state.config = cfg
    app.state.store = store

    @app.post(
        "/runs",
        response_model=RunCreateResponse,
        status_code=201,
    )
    async def create_run(body: RunCreateRequest) -> RunCreateResponse:  # noqa: D401
        driver = RunDriver(cfg, store=store)
        request = DriveRequest(
            prompt=body.prompt,
            profile_name=body.profile,
            model_override=body.model,
            reasoning_override=body.effort,
            reference_image=body.reference_image,
            max_revisions=body.max_revisions,
            role_model_overrides=body.role_models,
            role_reasoning_overrides=body.role_reasoning,
        )
        run, run_ctx, profile, role_profiles, max_revisions = driver.create_shell(request)

        task = asyncio.create_task(
            driver.continue_run(
                run=run,
                run_ctx=run_ctx,
                profile=profile,
                role_profiles=role_profiles,
                max_revisions=max_revisions,
                user_prompt=body.prompt,
            )
        )
        background[run.run_name] = task

        return RunCreateResponse(
            run_id=run.run_id,
            run_name=run.run_name,
            status_url=f"/runs/{run.run_name}/snapshot",
            events_url=f"/runs/{run.run_name}/events",
        )

    @app.get("/runs/{run_name}/snapshot")
    def get_snapshot(run_name: str) -> JSONResponse:
        path = cfg.runs_dir / run_name / "snapshot.json"
        if not path.is_file():
            raise HTTPException(404, detail=f"no snapshot for {run_name}")
        return JSONResponse(
            content=_read_json(path),
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/runs/{run_name}/events")
    def get_events(run_name: str, since: int = Query(default=0, ge=0)) -> JSONResponse:
        events = [e.model_dump() for e in store.read_events(run_name, since=since)]
        return JSONResponse({"events": events, "next_since": _next_since(events, since)})

    @app.get("/runs/{run_name}/revisions/{rev_name}")
    def get_revision(run_name: str, rev_name: str) -> JSONResponse:
        rev_json = cfg.runs_dir / run_name / "revisions" / rev_name / "revision.json"
        if not rev_json.is_file():
            raise HTTPException(404, detail=f"no revision {rev_name}")
        return JSONResponse(_read_json(rev_json))

    @app.get("/runs/{run_name}/revisions/{rev_name}/artifacts/{role}")
    def get_artifact(run_name: str, rev_name: str, role: str) -> FileResponse:
        path = _resolve_artifact(cfg, run_name, rev_name, role)
        if path is None or not path.is_file():
            raise HTTPException(404, detail=f"artifact role={role} not found")
        media_type, _ = mimetypes.guess_type(path.name)
        return FileResponse(path, media_type=media_type or "application/octet-stream")

    @app.get("/runs/{run_name}/review-summary")
    def get_review_summary(run_name: str) -> JSONResponse:
        # Find latest revision with a review.
        rev_dir = cfg.runs_dir / run_name / "revisions"
        if not rev_dir.is_dir():
            raise HTTPException(404, detail="no revisions yet")
        for rev in sorted(rev_dir.iterdir(), reverse=True):
            rs = rev / "review-summary.json"
            if rs.is_file():
                try:
                    review = ReviewSummary.model_validate_json(rs.read_text())
                except Exception:
                    raise HTTPException(500, detail="review summary is invalid") from None
                return JSONResponse(review.model_dump(mode="json"))
        raise HTTPException(404, detail="no review summary yet")

    @app.post(
        "/reference-images",
        response_model=ReferenceImageUploadResponse,
        status_code=201,
    )
    async def upload_reference_image(
        file: UploadFile = File(...),  # noqa: B008
    ) -> ReferenceImageUploadResponse:
        content = await file.read(MAX_REFERENCE_IMAGE_BYTES + 1)
        if not content:
            raise HTTPException(status_code=400, detail="reference image is empty")
        if len(content) > MAX_REFERENCE_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="reference image exceeds 10 MB",
            )
        content_type, ext = _validated_reference_image(content, file.content_type)
        upload_id = str(uuid.uuid4())
        upload_dir = cfg.repo_root / REFERENCE_UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / f"{upload_id}{ext}"
        dest.write_bytes(content)
        return ReferenceImageUploadResponse(
            upload_id=upload_id,
            reference_image=str(dest),
            filename=Path(file.filename or f"reference{ext}").name,
            content_type=content_type,
            size_bytes=len(content),
        )

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "runs_dir": str(cfg.runs_dir)}

    _mount_ui(app, cfg.repo_root / "web" / "dist")

    return app


def _read_json(path: Path) -> dict:
    import json

    return json.loads(path.read_text())


def _next_since(events: list[dict], current: int) -> int:
    if not events:
        return current
    return events[-1]["index"] + 1


_ROLE_PATHS = {
    "model_py": "model.py",
    "step": "model.step",
    "glb": "model.glb",
    "render_sheet": "render-sheet.png",
    "revision": "revision.json",
    "manifest": "artifact-manifest.json",
    "review": "review-summary.json",
    "build_metadata": "build-metadata.json",
    "render_metadata": "render-metadata.json",
    "inspect_summary": "inspect-summary.json",
    "designer_notes": "designer-notes.md",
}


def _resolve_artifact(cfg: HarnessConfig, run_name: str, rev_name: str, role: str) -> Path | None:
    base = cfg.runs_dir / run_name / "revisions" / rev_name
    if role in _ROLE_PATHS:
        return base / _ROLE_PATHS[role]
    if role.startswith("view_"):
        return base / "views" / f"{role[len('view_') :]}.png"
    return None


def _validated_reference_image(content: bytes, content_type: str | None) -> tuple[str, str]:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_type, ext = "image/png", ".png"
    elif content.startswith(b"\xff\xd8\xff"):
        detected_type, ext = "image/jpeg", ".jpg"
    else:
        raise HTTPException(status_code=415, detail="reference image must be PNG or JPEG")
    if content_type and content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(status_code=415, detail="reference image must be PNG or JPEG")
    return detected_type, ext


def _mount_ui(app: FastAPI, ui_dist: Path) -> None:
    """Serve the built browser UI when ``web/dist`` exists.

    REQ: FLU-D-001, FLU-D-004
    """

    assets_dir = ui_dist / "assets"
    index = ui_dist / "index.html"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="ui-assets")

    @app.get("/")
    def ui_index() -> HTMLResponse:
        if not index.is_file():
            raise HTTPException(404, detail="UI build not found; run npm --prefix web run build")
        return HTMLResponse(index.read_text(encoding="utf-8"))

    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    def ui_spa_fallback(full_path: str):
        first = full_path.split("/", 1)[0]
        if first in {"runs", "reference-images", "healthz", "docs", "openapi.json"}:
            raise HTTPException(404, detail="not found")
        static_file = _resolve_ui_static_file(ui_dist, full_path)
        if static_file is not None:
            media_type, _ = mimetypes.guess_type(static_file.name)
            return FileResponse(static_file, media_type=media_type)
        if not index.is_file():
            raise HTTPException(404, detail="UI build not found; run npm --prefix web run build")
        return HTMLResponse(index.read_text(encoding="utf-8"))


def _resolve_ui_static_file(ui_dist: Path, full_path: str) -> Path | None:
    """Resolve a built UI public file without allowing path traversal."""

    try:
        root = ui_dist.resolve()
        candidate = (root / full_path).resolve()
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


# Module-level singleton used by ``uvicorn formloop.api.app:app``.
app = create_app()
