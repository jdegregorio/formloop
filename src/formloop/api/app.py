from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from formloop.models import DesignRequest
from formloop.service import create_service


def create_app() -> FastAPI:
    service = create_service()
    app = FastAPI(title="Formloop Harness API", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    @app.post("/runs")
    def create_run(request: DesignRequest) -> dict:
        run = service.execute_run(request)
        return run.model_dump(mode="json")

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        try:
            return service.load_run(run_id).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/runs/{run_id}/events")
    def get_events(run_id: str) -> list[dict]:
        run_dir = service.store.run_dir(run_id)
        events_path = run_dir / "events.ndjson"
        if not events_path.exists():
            return []
        return [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @app.get("/runs/{run_id}/events/stream")
    def stream_events(run_id: str):
        run_dir = service.store.run_dir(run_id)
        events_path = run_dir / "events.ndjson"
        if not events_path.exists():
            raise HTTPException(status_code=404, detail="Event stream not found")

        def iter_events():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                yield line + "\n"

        return StreamingResponse(iter_events(), media_type="application/x-ndjson")

    @app.get("/artifacts/{run_id}/{artifact_path:path}")
    def get_artifact(run_id: str, artifact_path: str):
        run_dir = service.store.run_dir(run_id)
        path = (run_dir / artifact_path).resolve()
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_path}")
        return FileResponse(path)

    return app

