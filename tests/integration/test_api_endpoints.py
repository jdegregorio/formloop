"""HTTP API integration tests (FLH-F-025, FLH-D-019, FLH-NF-006).

Uses a stub driver + fixture config so the tests don't require OpenAI.
"""

from __future__ import annotations

import importlib
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
    ReviewOutcome,
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
        max_research_topics=8,
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
        effective_runtime=EffectiveRuntime(profile="dev_test", model="stub", reasoning="low"),
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "model.py").write_text("def build_model(params, context):\n    return None\n")
    (src / "model.step").write_text("ISO-STEP")
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
        model_py_src=src / "model.py",
        step_src=src / "model.step",
        glb_src=src / "model.glb",
        views_dir_src=views,
        render_sheet_src=src / "sheet.png",
    )
    revision, _ = store.persist_revision(run, bundle)
    store.attach_review(
        store.load_run(run.run_name),
        revision.revision_name,
        ReviewSummary(
            decision=ReviewDecision.pass_,
            outcome=ReviewOutcome.pass_,
            summary="The seeded geometry passed review.",
            next_step="Deliver this design.",
            key_findings=["ok"],
        ),
    )
    store.append_event(
        run.run_name,
        ProgressEvent(
            index=0,
            kind=ProgressEventKind.narration,
            message="we settled on the cube",
            phase="final",
        ),
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
        assert snap["input_summary"] == "seeded"
        assert snap["assumptions"] == []
        assert snap["final_answer"] is None
        assert snap["delivered_revision_name"] is None
        assert snap["latest_review_decision"] == "pass"
        # FLH-F-026 — latest narration is surfaced via /snapshot.
        assert snap["latest_narration"] == "we settled on the cube"
        assert snap["latest_narration_phase"] == "final"
        assert snap["latest_narration_index"] is not None

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
        r = await client.get(f"/runs/{run.run_name}/revisions/{revision.revision_name}")
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
        assert r.json()["schema_version"] == 2
        assert r.json()["outcome"] == "pass"
        assert "confidence" not in r.json()

        # unknown run
        r = await client.get("/runs/run-9999/snapshot")
        assert r.status_code == 404


async def test_reference_image_upload_validation(tmp_path: Path) -> None:
    config = _stub_config(tmp_path)
    app = create_app(config)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/reference-images",
            files={"file": ("ref.png", b"\x89PNG\r\n\x1a\npng-data", "image/png")},
        )
        assert r.status_code == 201
        payload = r.json()
        assert payload["content_type"] == "image/png"
        assert payload["reference_image"].endswith(".png")
        assert Path(payload["reference_image"]).is_file()

        bad = await client.post(
            "/reference-images",
            files={"file": ("ref.gif", b"GIF89a", "image/gif")},
        )
        assert bad.status_code == 415


async def test_create_run_accepts_uploaded_reference_image(
    tmp_path: Path, monkeypatch
) -> None:
    config = _stub_config(tmp_path)

    async def fake_continue_run(self, **kwargs):  # noqa: ANN001, ARG001
        return {"status": "succeeded"}

    api_app = importlib.import_module("formloop.api.app")
    monkeypatch.setattr(api_app.RunDriver, "continue_run", fake_continue_run)
    app = create_app(config)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        upload = await client.post(
            "/reference-images",
            files={"file": ("ref.jpg", b"\xff\xd8\xffjpeg-data", "image/jpeg")},
        )
        assert upload.status_code == 201
        reference_image = upload.json()["reference_image"]

        r = await client.post(
            "/runs",
            json={
                "prompt": "make this bracket",
                "profile": "dev_test",
                "reference_image": reference_image,
            },
        )
        assert r.status_code == 201
        run = app.state.store.load_run(r.json()["run_name"])
        assert run.reference_image == reference_image


async def test_create_run_accepts_role_overrides_and_exposes_effective_runtimes(
    tmp_path: Path, monkeypatch
) -> None:
    config = _stub_config(tmp_path)

    async def fake_continue_run(self, **kwargs):  # noqa: ANN001, ARG001
        return {"status": "succeeded"}

    api_app = importlib.import_module("formloop.api.app")
    monkeypatch.setattr(api_app.RunDriver, "continue_run", fake_continue_run)
    app = create_app(config)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/runs",
            json={
                "prompt": "a 20mm cube",
                "profile": "dev_test",
                "model": "global-api",
                "effort": "low",
                "role_models": {"cad_designer": "cad-api"},
                "role_reasoning": {"reviewer": "medium"},
            },
        )
        assert r.status_code == 201
        run_name = r.json()["run_name"]
        await app.state.background[run_name]

        run = app.state.store.load_run(run_name)
        assert run.effective_runtime.model == "global-api"
        assert run.effective_runtime.reasoning == "low"
        snap = (await client.get(f"/runs/{run_name}/snapshot")).json()
        assert snap["effective_role_runtimes"]["cad_designer"]["model"] == "cad-api"
        assert snap["effective_role_runtimes"]["manager_plan"]["model"] == "global-api"
        assert snap["effective_role_runtimes"]["reviewer"]["reasoning"] == "medium"


async def test_serves_built_ui_assets(tmp_path: Path) -> None:
    config = _stub_config(tmp_path)
    dist = tmp_path / "web" / "dist"
    assets = dist / "assets"
    brand = dist / "brand"
    assets.mkdir(parents=True)
    brand.mkdir()
    (dist / "index.html").write_text("<!doctype html><div id=\"root\"></div>")
    (assets / "app.js").write_text("console.log('ui')")
    (brand / "formloop-mark.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    app = create_app(config)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        index = await client.get("/")
        assert index.status_code == 200
        assert "root" in index.text

        asset = await client.get("/assets/app.js")
        assert asset.status_code == 200
        assert "ui" in asset.text

        brand_asset = await client.get("/brand/formloop-mark.png")
        assert brand_asset.status_code == 200
        assert brand_asset.headers["content-type"] == "image/png"

        nested = await client.get("/design/run-0001")
        assert nested.status_code == 200
        assert "root" in nested.text
