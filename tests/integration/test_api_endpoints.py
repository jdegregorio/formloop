"""HTTP API integration tests (FLH-F-025, FLH-D-019, FLH-NF-006).

Uses a stub driver + fixture config so the tests don't require OpenAI.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from formloop.api.app import create_app
from formloop.config.profiles import (
    ApiConfig,
    HarnessConfig,
    Profile,
    Timeouts,
)
from formloop.schemas import (
    EffectiveRuntime,
    ProgressEvent,
    ProgressEventKind,
    ReviewDecision,
    ReviewSummary,
    RevisionTrigger,
)
from formloop.store import RunStore
from formloop.store.run_store import CandidateBundle


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _stub_config(tmp_path: Path) -> HarnessConfig:
    return HarnessConfig(
        default_profile="dev_test",
        max_revisions=1,
        runs_dir=tmp_path / "runs",
        evals_dir=tmp_path / "evals",
        timeouts=Timeouts(
            cad_build=60, cad_render=60, cad_inspect=60, cad_compare=60, agent_run=60
        ),
        profiles={
            "dev_test": Profile(name="dev_test", model="stub", reasoning="low"),
        },
        api=ApiConfig(host="127.0.0.1", port=0, pid_file="x.pid", log_file="x.log"),
        repo_root=tmp_path,
    )


def _seed_run_with_revision(store: RunStore, tmp_path: Path):
    run, layout = store.create_run(
        input_summary="seeded",
        effective_runtime=EffectiveRuntime(
            profile="dev_test", model="stub", reasoning="low"
        ),
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "step.step").write_text("ISO-STEP")
    (src / "model.glb").write_bytes(b"glb")
    (src / "sheet.png").write_bytes(b"png-data")
    views = src / "views"
    views.mkdir()
    (views / "front.png").write_bytes(b"front-png")
    bundle = CandidateBundle(
        trigger=RevisionTrigger.initial,
        spec_snapshot={"kind": "cube"},
        designer_notes=None,
        known_risks=[],
        step_src=src / "step.step",
        glb_src=src / "model.glb",
        views_dir_src=views,
        render_sheet_src=src / "sheet.png",
    )
    revision, _ = store.persist_revision(run, bundle)
    store.attach_review(
        store.load_run(run.run_name),
        revision.revision_name,
        ReviewSummary(decision=ReviewDecision.pass_, confidence=0.95, key_findings=["ok"]),
    )
    store.append_event(
        run.run_name,
        ProgressEvent(index=0, kind=ProgressEventKind.delivered, message="done"),
    )
    return run, revision


async def test_snapshot_and_events_and_artifacts(tmp_path: Path) -> None:
    config = _stub_config(tmp_path)
    app = create_app(config)
    store = app.state.store
    run, revision = _seed_run_with_revision(store, tmp_path)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # healthz
        r = await client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        # snapshot
        r = await client.get(f"/runs/{run.run_name}/snapshot")
        assert r.status_code == 200
        snap = r.json()
        assert snap["run_name"] == run.run_name
        assert snap["latest_review_decision"] == "pass"

        # events with pagination
        r = await client.get(f"/runs/{run.run_name}/events")
        payload = r.json()
        assert r.status_code == 200
        assert len(payload["events"]) >= 1
        cursor = payload["next_since"]
        r2 = await client.get(f"/runs/{run.run_name}/events?since={cursor}")
        assert r2.status_code == 200
        assert r2.json()["events"] == []  # caught up

        # revision metadata
        r = await client.get(
            f"/runs/{run.run_name}/revisions/{revision.revision_name}"
        )
        assert r.status_code == 200
        assert r.json()["revision_name"] == revision.revision_name

        # artifact download — step file
        r = await client.get(
            f"/runs/{run.run_name}/revisions/{revision.revision_name}/artifacts/step"
        )
        assert r.status_code == 200
        assert b"ISO-STEP" in r.content

        # artifact — view_front
        r = await client.get(
            f"/runs/{run.run_name}/revisions/{revision.revision_name}/artifacts/view_front"
        )
        assert r.status_code == 200
        assert r.content == b"front-png"

        # review-summary
        r = await client.get(f"/runs/{run.run_name}/review-summary")
        assert r.status_code == 200
        assert r.json()["decision"] == "pass"

        # unknown run
        r = await client.get("/runs/run-9999/snapshot")
        assert r.status_code == 404
