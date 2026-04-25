"""Unit coverage for harness-owned CAD source validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from formloop.agents import RunContext
from formloop.agents.cad_designer import CadSourceResult
from formloop.agents.manager import ManagerPlan, NormalizedSpec
from formloop.config.profiles import Profile, Timeouts
from formloop.orchestrator.phase_context import PhaseRuntimeContext
from formloop.orchestrator.revision_loop import revision_loop_phase
from formloop.runtime.cad_cli import (
    BoundingBoxRecord,
    CadBuildResult,
    CadInspectResult,
    CadRenderResult,
)
from formloop.runtime.subprocess import CliError
from formloop.schemas import EffectiveRuntime, ProgressEvent, ProgressEventKind, ReviewDecision
from formloop.schemas.review_summary import ReviewSummary
from formloop.store import RunStore

pytestmark = pytest.mark.asyncio


class _FakeContext:
    def __init__(self, store: RunStore, sources: list[CadSourceResult]) -> None:
        self.store = store
        self.sources = sources
        self.designer_inputs: list[str] = []
        self.events: list[ProgressEvent] = []
        self.persist_count = 0

    async def narrate(self, *args, **kwargs) -> None:
        return None

    def emit(
        self,
        run_name: str,
        kind: ProgressEventKind,
        message: str,
        *,
        data: dict | None = None,
        phase: str | None = None,
        narration_error: str | None = None,
    ) -> None:
        event = self.store.append_event(
            run_name,
            ProgressEvent(
                index=0,
                kind=kind,
                message=message,
                data=data or {},
                phase=phase,
                narration_error=narration_error,
            ),
        )
        self.events.append(event)

    def load_run(self, run_name: str):
        return self.store.load_run(run_name)

    def save_run(self, run) -> None:
        self.store.save_run(run)

    def attach_review(self, run, revision_name: str, review: ReviewSummary) -> None:
        self.store.attach_review(run, revision_name, review)

    def persist_revision(self, run, bundle):
        self.persist_count += 1
        return self.store.persist_revision(run, bundle)

    def load_snapshot(self, run_name: str):
        return self.store.load_snapshot(run_name)

    async def design_revision(
        self, designer_input: str, run_ctx: RunContext, profile: Profile
    ) -> CadSourceResult:
        self.designer_inputs.append(designer_input)
        return self.sources.pop(0)

    async def review_revision(self, payload: list[dict[str, Any]], profile: Profile):
        raise AssertionError("review_phase is monkeypatched in these tests")

    async def finalize(self, payload: dict[str, Any], profile: Profile):
        raise AssertionError("not used")


def _source(note: str = "source") -> CadSourceResult:
    return CadSourceResult(
        source=(
            "from build123d import Box\n\n"
            "def build_model(params: dict, context: object):\n"
            "    return Box(20, 20, 20)\n"
        ),
        revision_notes=note,
        known_risks=[],
        intended_features=["20mm cube"],
        self_reported_dimensions={"size": 20},
    )


def _plan() -> ManagerPlan:
    return ManagerPlan(
        normalized_spec=NormalizedSpec(
            name="cube",
            type="component",
            units="mm",
            design_intent="Simple calibration cube.",
            features=["Solid cube body"],
            interfaces=[],
            constraints=["edge length must be 20 mm"],
            preferences=[],
            manufacturing_method=None,
            key_dimension_parameters={"size_mm": 20},
        ),
        assumptions=[],
        research_topics=[],
        design_brief="A simple 20mm cube.",
    )


def _runtime(tmp_path: Path):
    store = RunStore(tmp_path / "runs")
    run, layout = store.create_run(
        input_summary="a 20mm cube",
        effective_runtime=EffectiveRuntime(profile="dev_test", model="stub", reasoning="low"),
    )
    source_dir = layout.root / "_work" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    profile = Profile(name="dev_test", model="stub", reasoning="low")
    run_ctx = RunContext(
        run_name=run.run_name,
        run_root=layout.root,
        source_dir=source_dir,
        profile=profile,
        timeouts=Timeouts(
            cad_build=1,
            cad_render=1,
            cad_inspect=1,
            cad_compare=1,
            agent_run=1,
        ),
    )
    runtime = PhaseRuntimeContext(
        run=run, run_ctx=run_ctx, profile=profile, user_prompt="a 20mm cube"
    )
    return store, runtime


def _fake_build(*, model_path: Path, output_dir: Path, **kwargs) -> CadBuildResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "model.step").write_text("step", encoding="utf-8")
    (output_dir / "model.glb").write_text("glb", encoding="utf-8")
    metadata = output_dir / "build-metadata.json"
    metadata.write_text("{}", encoding="utf-8")
    return CadBuildResult(
        command="cad build",
        summary="built",
        output_dir=str(output_dir),
        metadata_path=str(metadata),
        artifacts=[],
        bounding_box=BoundingBoxRecord(
            min_corner=[0, 0, 0], max_corner=[20, 20, 20], size=[20, 20, 20]
        ),
        volume=8000,
    )


def _fake_inspect(artifact_path: Path, **kwargs) -> CadInspectResult:
    return CadInspectResult(
        command="cad inspect summary",
        summary="inspected",
        artifact_path=str(artifact_path),
        mode="summary",
        data={"bbox": {"size": [20, 20, 20]}},
    )


def _fake_render(*, glb_path: Path, output_dir: Path, **kwargs) -> CadRenderResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = output_dir / "render-metadata.json"
    metadata.write_text("{}", encoding="utf-8")
    (output_dir / "sheet.png").write_bytes(b"sheet")
    for name in ("front", "back", "left", "right", "top", "bottom", "iso"):
        (output_dir / f"{name}.png").write_bytes(name.encode())
    return CadRenderResult(
        command="cad render",
        summary="rendered",
        input_glb=str(glb_path),
        output_dir=str(output_dir),
        metadata_path=str(metadata),
        artifacts=[],
        blender_bin="stub",
        render_spec={},
    )


async def _passing_review(*args, **kwargs) -> ReviewSummary:
    return ReviewSummary(
        decision=ReviewDecision.pass_,
        confidence=0.9,
        key_findings=["looks good"],
    )


async def _revising_review(*args, **kwargs) -> ReviewSummary:
    return ReviewSummary(
        decision=ReviewDecision.revise,
        confidence=0.4,
        key_findings=["dimensions off"],
        revision_instructions="tighten the fit",
    )


async def test_successful_first_source_creates_one_persisted_revision(
    tmp_path, monkeypatch
) -> None:
    store, runtime = _runtime(tmp_path)
    ctx = _FakeContext(store, [_source()])
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", _fake_build)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_inspect_summary", _fake_inspect)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_render", _fake_render)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.review_phase", _passing_review)

    delivered = await revision_loop_phase(ctx, runtime, plan=_plan(), findings=[], max_revisions=1)

    fresh = store.load_run(runtime.run.run_name)
    assert delivered == "rev-001"
    assert fresh.revisions == ["rev-001"]
    assert ctx.persist_count == 1
    attempt_dir = runtime.run_root / "_work" / "source_attempts" / "attempt-001"
    assert (attempt_dir / "model.py").is_file()
    validation = json.loads((attempt_dir / "validation-result.json").read_text())
    assert [cmd["command"] for cmd in validation["commands"]] == [
        "cad build",
        "cad inspect summary",
        "cad render",
    ]
    assert all(cmd["status"] == "ok" for cmd in validation["commands"])
    assert all(cmd["returncode"] == 0 for cmd in validation["commands"])
    assert all("duration_s" in cmd for cmd in validation["commands"])
    assert any(ev.kind is ProgressEventKind.cad_validation_completed for ev in ctx.events)


async def test_build_failure_sends_feedback_and_retries(tmp_path, monkeypatch) -> None:
    store, runtime = _runtime(tmp_path)
    ctx = _FakeContext(store, [_source("bad"), _source("fixed")])
    calls = {"build": 0}

    def flaky_build(*args, **kwargs):
        calls["build"] += 1
        if calls["build"] == 1:
            raise CliError(
                cmd=["cad", "build"],
                returncode=1,
                stdout="",
                stderr="NameError: bad_symbol",
            )
        return _fake_build(*args, **kwargs)

    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", flaky_build)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_inspect_summary", _fake_inspect)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_render", _fake_render)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.review_phase", _passing_review)

    delivered = await revision_loop_phase(ctx, runtime, plan=_plan(), findings=[], max_revisions=1)

    assert delivered == "rev-001"
    assert len(ctx.designer_inputs) == 2
    assert "CAD_VALIDATION_FAILURE_FEEDBACK" in ctx.designer_inputs[1]
    failed = runtime.run_root / "_work" / "source_attempts" / "attempt-001"
    assert (failed / "failure-feedback.json").is_file()
    assert any(ev.kind is ProgressEventKind.cad_validation_failed for ev in ctx.events)


async def test_build_failure_with_traceback_sends_to_feedback(tmp_path, monkeypatch) -> None:
    store, runtime = _runtime(tmp_path)
    ctx = _FakeContext(store, [_source("bad"), _source("fixed")])
    calls = {"build": 0}

    def flaky_build(*args, **kwargs):
        calls["build"] += 1
        if calls["build"] == 1:
            json_stderr = json.dumps({
                "error": {
                    "type": "BuildError",
                    "message": "msg",
                    "traceback": "Traceback (most recent call last): ...",
                    "exit_code": 1
                }
            })
            raise CliError(
                cmd=["cad", "build"],
                returncode=1,
                stdout="",
                stderr=json_stderr,
            )
        return _fake_build(*args, **kwargs)

    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", flaky_build)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_inspect_summary", _fake_inspect)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_render", _fake_render)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.review_phase", _passing_review)

    delivered = await revision_loop_phase(ctx, runtime, plan=_plan(), findings=[], max_revisions=1)

    assert delivered == "rev-001"
    assert len(ctx.designer_inputs) == 2
    assert "Traceback (from cad-cli):" in ctx.designer_inputs[1]
    assert "Traceback (most recent call last): ..." in ctx.designer_inputs[1]


async def test_render_failure_sends_feedback_and_retries(tmp_path, monkeypatch) -> None:
    store, runtime = _runtime(tmp_path)
    ctx = _FakeContext(store, [_source("render bad"), _source("render fixed")])
    calls = {"render": 0}

    def flaky_render(*args, **kwargs):
        calls["render"] += 1
        if calls["render"] == 1:
            raise CliError(
                cmd=["cad", "render"],
                returncode=1,
                stdout="",
                stderr="Blender failed",
            )
        return _fake_render(*args, **kwargs)

    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", _fake_build)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_inspect_summary", _fake_inspect)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_render", flaky_render)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.review_phase", _passing_review)

    delivered = await revision_loop_phase(ctx, runtime, plan=_plan(), findings=[], max_revisions=1)

    assert delivered == "rev-001"
    assert len(ctx.designer_inputs) == 2
    assert '"failed_phase": "render"' in ctx.designer_inputs[1]
    assert calls["render"] == 2


async def test_persisted_revisions_without_review_pass_are_not_delivered(
    tmp_path, monkeypatch
) -> None:
    """Regression: a revision is "delivered" only when review accepts it.

    Previously the loop set ``delivered`` immediately after persistence, so
    exhausting ``max_revisions`` with revise-decisions still returned the
    last revision name and the run was reported as succeeded.
    """

    store, runtime = _runtime(tmp_path)
    ctx = _FakeContext(store, [_source("first"), _source("second")])
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", _fake_build)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_inspect_summary", _fake_inspect)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_render", _fake_render)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.review_phase", _revising_review)

    delivered = await revision_loop_phase(ctx, runtime, plan=_plan(), findings=[], max_revisions=2)

    fresh = store.load_run(runtime.run.run_name)
    assert delivered is None
    assert fresh.revisions == ["rev-001", "rev-002"]
    assert ctx.persist_count == 2


async def test_exhausted_validation_retries_persist_no_revision(tmp_path, monkeypatch) -> None:
    store, runtime = _runtime(tmp_path)
    ctx = _FakeContext(store, [_source(str(i)) for i in range(4)])

    def always_fails(*args, **kwargs):
        raise CliError(
            cmd=["cad", "build"],
            returncode=1,
            stdout="",
            stderr="SyntaxError: invalid syntax",
        )

    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", always_fails)

    delivered = await revision_loop_phase(ctx, runtime, plan=_plan(), findings=[], max_revisions=1)

    fresh = store.load_run(runtime.run.run_name)
    assert delivered is None
    assert fresh.revisions == []
    assert ctx.persist_count == 0
    assert len(ctx.designer_inputs) == 4
    assert (runtime.run_root / "_work" / "source_attempts" / "attempt-004").is_dir()
