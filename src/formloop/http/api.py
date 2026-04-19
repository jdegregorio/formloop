"""FastAPI app for the Formloop harness."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from ..models import RunCreateRequest, RunCreateResponse
from ..services.harness import HarnessService


def create_app(harness: HarnessService | None = None) -> FastAPI:
    # Req: FLH-F-025, FLH-D-019
    service = harness or HarnessService()
    app = FastAPI(title="Formloop Harness API", version="0.1.0")
    tasks: dict[str, asyncio.Task[object]] = {}

    @app.post("/runs", response_model=RunCreateResponse)
    async def create_run(request: RunCreateRequest) -> RunCreateResponse:
        run = service.begin_run(request)
        tasks[run.run_id] = asyncio.create_task(service.continue_run(run.run_name, request))
        snapshot_path = service.store.run_dir(run.run_name) / "snapshot.json"
        return RunCreateResponse(
            run_id=run.run_id,
            run_name=run.run_name,
            status=run.status,
            snapshot_path=str(snapshot_path),
        )

    @app.get("/runs/{run_name}")
    async def get_run_snapshot(run_name: str) -> dict[str, Any]:
        try:
            return service.store.load_snapshot(run_name).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/runs/{run_name}/events")
    async def get_run_events(run_name: str) -> list[dict[str, Any]]:
        return [event.model_dump(mode="json") for event in service.store.list_events(run_name)]

    @app.get("/runs/{run_name}/revisions/{revision_name}")
    async def get_revision(run_name: str, revision_name: str) -> dict[str, Any]:
        path = service.store.run_dir(run_name) / "revisions" / revision_name / "revision.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="revision not found")
        return service.store.load_run(run_name).model_dump(mode="json") | {
            "revision": path.read_text(encoding="utf-8")
        }

    @app.get("/runs/{run_name}/revisions/{revision_name}/review")
    async def get_review(run_name: str, revision_name: str) -> dict[str, Any]:
        path = service.store.run_dir(run_name) / "revisions" / revision_name / "review-summary.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="review not found")
        return {"review": path.read_text(encoding="utf-8")}

    @app.get("/runs/{run_name}/artifacts/{run_token}/{revision_name}/{artifact_role}")
    async def get_artifact(
        run_name: str,
        run_token: str,
        revision_name: str,
        artifact_role: str,
    ) -> FileResponse:
        del run_token
        revision_dir = service.store.run_dir(run_name) / "revisions" / revision_name
        candidates = {
            "step": revision_dir / "step.step",
            "glb": revision_dir / "model.glb",
            "render_sheet": revision_dir / "render-sheet.png",
        }
        if artifact_role.startswith("view_"):
            candidates[artifact_role] = (
                revision_dir / "views" / f"{artifact_role.removeprefix('view_')}.png"
            )
        path = candidates.get(artifact_role)
        if path is None or not path.exists():
            raise HTTPException(status_code=404, detail="artifact not found")
        return FileResponse(path)

    return app
