"""Unit tests: agents build cleanly from a profile and declare the right surface.

REQ: FLH-D-007, FLH-D-008, FLH-D-009, FLH-D-010, FLH-D-017
"""

from __future__ import annotations

import pytest

from formloop.agents import (
    CadRevisionResult,
    CadSourceResult,
    ManagerFinalAnswer,
    ManagerPlan,
    RunContext,
    build_cad_designer,
    build_judge,
    build_manager_final,
    build_manager_plan,
    build_reviewer,
)
from formloop.config.profiles import Profile, Timeouts
from formloop.schemas import JudgeOutput, ReviewSummary


@pytest.fixture()
def profile() -> Profile:
    return Profile(name="dev_test", model="gpt-5.4-nano", reasoning="low")


def _underlying_type(agent):
    ot = agent.output_type
    # lenient_output wraps in AgentOutputSchema → underlying type is at
    # ._output_type or accessible via .output_type attribute depending on SDK.
    return getattr(ot, "_output_type", getattr(ot, "output_type", ot))


def test_manager_planner_structured_output(profile: Profile) -> None:
    agent = build_manager_plan(profile)
    assert agent.model == "gpt-5.4-nano"
    assert _underlying_type(agent) is ManagerPlan
    assert agent.model_settings.reasoning is not None
    assert agent.model_settings.reasoning.effort == "low"


def test_manager_final_structured_output(profile: Profile) -> None:
    agent = build_manager_final(profile)
    assert _underlying_type(agent) is ManagerFinalAnswer


def test_cad_designer_is_source_only(profile: Profile, tmp_path) -> None:
    run_root = tmp_path / "run-0001"
    source_dir = run_root / "_work" / "source"
    source_dir.mkdir(parents=True)
    run_ctx = RunContext(
        run_name="run-0001",
        run_root=run_root,
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
    agent = build_cad_designer(profile, run_ctx)
    assert _underlying_type(agent) is CadSourceResult
    tool_names = {getattr(t, "name", t.__class__.__name__) for t in agent.tools}
    assert {"read_model_source", "run_build_self_check", "python_help", "python_inspect"} <= (
        tool_names
    )
    assert any("ApplyPatch" in name or "apply_patch" in name for name in tool_names)
    assert CadRevisionResult is not CadSourceResult
    assert "bd_warehouse" in agent.instructions
    assert "py_gearworks" in agent.instructions
    assert "bd_vslot" not in agent.instructions
    assert "BUILD123D ECOSYSTEM CHEAT SHEET" in agent.instructions


def test_reviewer_and_judge_modes(profile: Profile) -> None:
    review = build_reviewer(profile)
    judge = build_judge(profile)
    assert _underlying_type(review) is ReviewSummary
    assert _underlying_type(judge) is JudgeOutput
    # The two modes must use distinct instruction bodies (FLH-F-006/014 differ).
    assert review.instructions != judge.instructions
