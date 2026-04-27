"""RunDriver emits narration events at each milestone.

REQ: FLH-F-024, FLH-F-026, FLH-D-013, FLH-D-025, FLH-NF-010

The driver must:

* call the Narrator at each milestone (plan, revision-start, revision-built,
  final) without crashing when the agents are stubbed;
* never leak run names, revision names, or filesystem paths into narration
  text (FLH-D-013, FLH-D-025) — the orchestrator passes only sanitized
  ``NarrationInput`` payloads, so a recording stub can assert this directly;
* keep the run alive when narration raises (FLH-NF-010);
* roll the latest narration into ``snapshot.json`` for the polling clients.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from formloop.agents.cad_designer import CadSourceResult
from formloop.agents.manager import (
    AssumptionProposal,
    ManagerFinalAnswer,
    ManagerPlan,
    NormalizedSpec,
)
from formloop.agents.narrator import NarrationInput
from formloop.config.profiles import (
    ApiConfig,
    HarnessConfig,
    Profile,
    Timeouts,
)
from formloop.orchestrator.narrator import Narrator
from formloop.orchestrator.run_driver import DriveRequest, RunDriver
from formloop.runtime.subprocess import CliError
from formloop.schemas import ProgressEventKind

pytestmark = pytest.mark.asyncio


@dataclass
class _FakeResult:
    final_output: Any


def _stub_config(tmp_path: Path) -> HarnessConfig:
    return HarnessConfig(
        default_profile="dev_test",
        max_revisions=1,
        max_research_topics=8,
        max_research_turns=3,
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


def _install_runner_stub(monkeypatch) -> None:
    """Replace ``Runner.run`` with a deterministic dispatcher.

    Returns canned outputs for the manager, the cad designer (source only),
    and the manager-final agent. Researcher isn't called because the plan
    has no research topics.
    """

    def fake_cad_build(*args, **kwargs):
        raise CliError(
            cmd=["cad", "build"],
            returncode=1,
            stdout="",
            stderr="stubbed build failure",
        )

    async def fake_run(agent, input, *args, **kwargs):  # noqa: A002
        name = getattr(agent, "name", "")
        if name == "manager_planner":
            return _FakeResult(
                final_output=ManagerPlan(
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
                    assumptions=[AssumptionProposal(topic="size", assumption="20mm cube")],
                    research_topics=[],
                    design_brief="A simple 20mm cube.",
                )
            )
        if name == "cad_designer":
            return _FakeResult(
                final_output=CadSourceResult(
                    source=(
                        "from build123d import Box\n\n"
                        "def build_model(params: dict, context: object):\n"
                        "    return Box(20, 20, 20)\n"
                    ),
                    revision_notes="stub source",
                    known_risks=[],
                    self_reported_dimensions={"size": 20},
                )
            )
        if name == "manager_final":
            return _FakeResult(
                final_output=ManagerFinalAnswer(
                    text="we did not deliver a revision",
                    delivered_revision_name=None,
                )
            )
        raise AssertionError(f"unexpected agent in stub: {name!r}")

    monkeypatch.setattr("formloop.orchestrator.run_driver.Runner.run", fake_run)
    monkeypatch.setattr("formloop.orchestrator.revision_loop.cad_build", fake_cad_build)


async def _drive(tmp_path: Path, monkeypatch, narrator: Narrator) -> tuple[Any, list]:
    _install_runner_stub(monkeypatch)
    config = _stub_config(tmp_path)
    captured = []
    driver = RunDriver(
        config,
        narrator=narrator,
        event_hook=lambda ev: captured.append(ev),
    )
    result = await driver.run(DriveRequest(prompt="a 20mm cube"))
    return result, captured


async def test_narration_events_emitted_at_each_milestone(tmp_path, monkeypatch) -> None:
    result, events = await _drive(tmp_path, monkeypatch, narrator=Narrator(fallback_only=True))
    narration = [ev for ev in events if ev.kind is ProgressEventKind.narration]
    phases = [ev.phase for ev in narration]

    # Post-op-feedback: we narrate only at milestones that carry run-specific
    # content — plan-end (normalized spec + assumptions) and revision-built
    # (designer output). No research (empty topics), no retry (first attempt),
    # no review (designer stub fails so we never reach review), no finalize.
    assert phases == ["plan", "revision"], phases
    # Fallback strings should be the captured messages (LLM is off).
    assert any("normalized" in ev.message for ev in narration)
    assert any(
        "build" in ev.message.lower() or "designer" in ev.message.lower() for ev in narration
    )
    # Snapshot reflects the latest one.
    snap = driver_snapshot(tmp_path, result["run_name"])
    assert snap["latest_narration"] == narration[-1].message
    assert snap["latest_narration_phase"] == narration[-1].phase
    assert snap["latest_narration_index"] == narration[-1].index


async def test_narration_inputs_carry_no_identifiers(tmp_path, monkeypatch) -> None:
    """The orchestrator must hand the Narrator only sanitized payloads.

    REQ: FLH-D-013, FLH-D-025 — no run names, revision names, or paths.
    """

    seen: list[NarrationInput] = []

    class RecordingNarrator(Narrator):
        async def narrate(self, payload, *, fallback):  # type: ignore[override]
            seen.append(payload)
            return fallback, None

    await _drive(tmp_path, monkeypatch, narrator=RecordingNarrator(fallback_only=True))

    forbidden_substrings = ("run-", "rev-", "/var/", ".step", ".glb", ".png")
    for payload in seen:
        text_blob = " ".join(
            [payload.phase, payload.just_completed, payload.next_step, payload.why]
        )
        for needle in forbidden_substrings:
            assert needle not in text_blob, f"narration payload leaked {needle!r}: {payload!r}"


async def test_run_survives_narrator_failure(tmp_path, monkeypatch) -> None:
    class BrokenNarrator(Narrator):
        async def narrate(self, payload, *, fallback):  # type: ignore[override]
            raise RuntimeError("narrator offline")

    result, events = await _drive(
        tmp_path, monkeypatch, narrator=BrokenNarrator(fallback_only=True)
    )
    # Run still completed (no delivered revision because designer stub fails).
    assert result["status"] in ("succeeded", "failed")
    narration = [ev for ev in events if ev.kind is ProgressEventKind.narration]
    assert narration, "driver should emit narration events even when narrator raises"
    # Each narration event should carry the fallback text + the error string.
    for ev in narration:
        assert ev.narration_error is not None
        assert ev.message  # fallback message present


def driver_snapshot(tmp_path: Path, run_name: str) -> dict:
    import json

    path = tmp_path / "runs" / run_name / "snapshot.json"
    return json.loads(path.read_text())


async def test_run_driver_coordinates_phase_functions(tmp_path, monkeypatch) -> None:
    """RunDriver should delegate orchestration to phase modules in order."""

    _install_runner_stub(monkeypatch)
    config = _stub_config(tmp_path)
    driver = RunDriver(config, narrator=Narrator(fallback_only=True))

    calls: list[str] = []

    async def fake_plan(ctx, runtime, *, max_research_topics):  # noqa: ARG001
        assert ctx is driver
        calls.append("plan")
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
            design_brief="brief",
        )

    async def fake_research(ctx, runtime, *, plan):  # noqa: ARG001
        assert ctx is driver
        calls.append("research")
        return []

    async def fake_revision(ctx, runtime, *, plan, findings, max_revisions):
        assert ctx is driver
        calls.append("revision")
        return None

    monkeypatch.setattr("formloop.orchestrator.run_driver.plan_phase", fake_plan)
    monkeypatch.setattr("formloop.orchestrator.run_driver.research_phase", fake_research)
    monkeypatch.setattr("formloop.orchestrator.run_driver.revision_loop_phase", fake_revision)

    result = await driver.run(DriveRequest(prompt="a 20mm cube"))
    assert calls == ["plan", "research", "revision"]
    assert result["status"] == "failed"


async def test_run_driver_reports_failed_when_revisions_persisted_without_pass(
    tmp_path, monkeypatch
) -> None:
    """Persisted-but-unreviewed revisions must not be reported as a success.

    The revision loop returns ``None`` when no revision passed review; the
    driver must surface ``failed`` and a status_detail that names the
    unresolved review (not the misleading 'no revision bundle was delivered').
    """

    _install_runner_stub(monkeypatch)
    config = _stub_config(tmp_path)
    driver = RunDriver(config, narrator=Narrator(fallback_only=True))

    async def fake_plan(ctx, runtime, *, max_research_topics):  # noqa: ARG001
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
            design_brief="brief",
        )

    async def fake_research(ctx, runtime, *, plan):  # noqa: ARG001
        return []

    async def fake_revision(ctx, runtime, *, plan, findings, max_revisions):
        # Simulate a loop that persisted revisions but never got a review pass.
        run = ctx.load_run(runtime.run.run_name)
        run.revisions = ["rev-001", "rev-002"]
        ctx.save_run(run)
        return None

    monkeypatch.setattr("formloop.orchestrator.run_driver.plan_phase", fake_plan)
    monkeypatch.setattr("formloop.orchestrator.run_driver.research_phase", fake_research)
    monkeypatch.setattr("formloop.orchestrator.run_driver.revision_loop_phase", fake_revision)

    result = await driver.run(DriveRequest(prompt="a 20mm cube"))
    assert result["status"] == "failed"
    assert result["delivered_revision"] is None

    persisted = driver.store.load_run(result["run_name"])
    assert persisted.status.value == "failed"
    assert persisted.status_detail == "2 revision(s) persisted but none passed review"


async def test_research_topic_uses_configured_max_turns(tmp_path, monkeypatch) -> None:
    config = _stub_config(tmp_path)
    config = replace(config, max_research_turns=3)
    driver = RunDriver(config, narrator=Narrator(fallback_only=True))

    captured: dict[str, Any] = {}

    async def fake_run(agent, input, *args, **kwargs):  # noqa: A002
        captured["agent_name"] = getattr(agent, "name", "")
        captured["input"] = input
        captured["max_turns"] = kwargs.get("max_turns")
        return _FakeResult(
            final_output=SimpleNamespace(
                model_dump=lambda: {"topic": "topic-123", "summary": "ok", "citations": []}
            )
        )

    monkeypatch.setattr("formloop.orchestrator.run_driver.Runner.run", fake_run)
    finding = await driver.research_topic("topic-123", config.profile("dev_test"))

    assert captured["agent_name"] == "design_researcher"
    assert captured["max_turns"] == 3
    assert "Topic: topic-123" in captured["input"]
    assert "Turn budget: 3 total turns." in captured["input"]
    assert "Final answer limit: 500 words maximum." in captured["input"]
    assert finding["topic"] == "topic-123"
