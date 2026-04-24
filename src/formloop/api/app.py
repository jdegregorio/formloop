"""FastAPI polling API for the Formloop harness.

REQ: FLH-F-025, FLH-D-019, FLH-D-022, FLH-NF-004, FLH-NF-006
"""

from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from ..config.env import load_env_local
from ..config.profiles import HarnessConfig, load_config
from ..orchestrator import RunDriver
from ..orchestrator.run_driver import DriveRequest
from ..schemas import RunCreateRequest, RunCreateResponse
from ..store import RunStore


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
            reference_image=body.reference_image,
            max_revisions=body.max_revisions,
        )
        run, run_ctx, profile, max_revisions = driver.create_shell(request)

        task = asyncio.create_task(
            driver.continue_run(
                run=run,
                run_ctx=run_ctx,
                profile=profile,
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
                return JSONResponse(_read_json(rs))
        raise HTTPException(404, detail="no review summary yet")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "runs_dir": str(cfg.runs_dir)}

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


# Module-level singleton used by ``uvicorn formloop.api.app:app``.
app = create_app()
