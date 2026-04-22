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

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from formloop.agents.cad_designer import CadRevisionResult
from formloop.agents.manager import (
    AssumptionProposal,
    ManagerFinalAnswer,
    ManagerPlan,
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
from formloop.schemas import ProgressEventKind, ReviewDecision, ReviewSummary


pytestmark = pytest.mark.asyncio


@dataclass
class _FakeResult:
    final_output: Any


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


def _install_runner_stub(monkeypatch) -> None:
    """Replace ``Runner.run`` with a deterministic dispatcher.

    Returns canned outputs for the manager, the cad designer (a "build
    failed" result so the loop short-circuits without touching cad-cli),
    and the manager-final agent. Researcher isn't called because the plan
    has no research topics.
    """

    async def fake_run(agent, input, *args, **kwargs):  # noqa: A002
        name = getattr(agent, "name", "")
        if name == "manager_planner":
            return _FakeResult(
                final_output=ManagerPlan(
                    normalized_spec={"kind": "cube", "size_mm": 20},
                    assumptions=[
                        AssumptionProposal(topic="size", assumption="20mm cube")
                    ],
                    research_topics=[],
                    design_brief="A simple 20mm cube.",
                )
            )
        if name == "cad_designer":
            return _FakeResult(
                final_output=CadRevisionResult(
                    build_ok=False,
                    inspect_ok=False,
                    render_ok=False,
                    revision_notes="stub failed",
                    known_risks=[],
                    dimensions={},
                    build_errors=["stubbed failure"],
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
    result, events = await _drive(
        tmp_path, monkeypatch, narrator=Narrator(fallback_only=True)
    )
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
        "build" in ev.message.lower() or "designer" in ev.message.lower()
        for ev in narration
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
            assert needle not in text_blob, (
                f"narration payload leaked {needle!r}: {payload!r}"
            )


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


async def test_run_fails_when_revision_loop_exhausts_without_accepted_revision(
    tmp_path, monkeypatch
) -> None:
    config = _stub_config(tmp_path)
    driver = RunDriver(config, narrator=Narrator(fallback_only=True))

    async def fake_plan(run, prompt, profile):  # noqa: ARG001
        return ManagerPlan(
            normalized_spec={"kind": "plate_with_holes"},
            assumptions=[],
            research_topics=[],
            design_brief="plate with two holes",
        )

    async def fake_research(run, plan, profile):  # noqa: ARG001
        return []

    async def fake_revision_loop(
        *,
        run,
        run_ctx,
        plan,
        findings,
        profile,
        max_revisions,
        user_prompt,
    ):  # noqa: ARG001
        fresh = driver.store.load_run(run.run_name)
        fresh.current_revision_id = "rev-001"
        driver.store.save_run(fresh)
        rev_dir = tmp_path / "runs" / run.run_name / "revisions" / "rev-001"
        rev_dir.mkdir(parents=True, exist_ok=True)
        review_path = rev_dir / "review-summary.json"
        review_path.write_text(
            ReviewSummary(
                decision=ReviewDecision.revise,
                confidence=0.9,
                key_findings=["hole diameter is wrong"],
                revision_instructions="fix the holes",
            ).model_dump_json(indent=2)
        )
        driver.store._refresh_snapshot(fresh, driver.store.layout(run.run_name))  # noqa: SLF001
        return None

    async def fake_finalize(run, plan, delivered_rev_name, profile):  # noqa: ARG001
        raise AssertionError("finalize should not run without an accepted revision")

    monkeypatch.setattr(driver, "_plan", fake_plan)
    monkeypatch.setattr(driver, "_research", fake_research)
    monkeypatch.setattr(driver, "_revision_loop", fake_revision_loop)
    monkeypatch.setattr(driver, "_finalize", fake_finalize)

    result = await driver.run(DriveRequest(prompt="plate"))

    assert result["status"] == "failed"
    assert result["delivered_revision"] is None
    assert result["final_answer"] is None
    stored = driver.store.load_run(result["run_name"])
    assert stored.status.value == "failed"
    assert "reviewer approved" in (stored.status_detail or "")


def driver_snapshot(tmp_path: Path, run_name: str) -> dict:
    import json

    path = tmp_path / "runs" / run_name / "snapshot.json"
    return json.loads(path.read_text())
