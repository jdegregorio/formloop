"""Unit tests: agents build cleanly from a profile and declare the right surface.

REQ: FLH-D-007, FLH-D-008, FLH-D-009, FLH-D-010, FLH-D-017
"""

from __future__ import annotations

import pytest

from formloop.agents import (
    CadRevisionResult,
    ManagerFinalAnswer,
    ManagerPlan,
    ResearchFinding,
    build_cad_designer,
    build_design_researcher,
    build_manager_final,
    build_manager_plan,
    build_quality_specialist_judge,
    build_quality_specialist_review,
)
from formloop.config.profiles import Profile
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


def test_design_researcher_has_web_search(profile: Profile) -> None:
    agent = build_design_researcher(profile)
    assert _underlying_type(agent) is ResearchFinding
    tool_names = [t.__class__.__name__ for t in agent.tools]
    assert "WebSearchTool" in tool_names


def test_cad_designer_registers_four_tools(profile: Profile) -> None:
    agent = build_cad_designer(profile)
    assert _underlying_type(agent) is CadRevisionResult
    # Four tools: write_model, build_model_cli, inspect_model, render_model.
    tool_names = {getattr(t, "name", t.__class__.__name__) for t in agent.tools}
    assert {"write_model", "build_model_cli", "inspect_model", "render_model"} <= tool_names


def test_quality_specialist_modes(profile: Profile) -> None:
    review = build_quality_specialist_review(profile)
    judge = build_quality_specialist_judge(profile)
    assert _underlying_type(review) is ReviewSummary
    assert _underlying_type(judge) is JudgeOutput
    # The two modes must use distinct instruction bodies (FLH-F-006/014 differ).
    assert review.instructions != judge.instructions


def test_quality_specialist_prompts_are_multimodal(profile: Profile) -> None:
    """The reviewer/judge must instruct the model to use images + checklist.

    Guards the multi-modal intent of the Quality Specialist (FLH-F-007,
    FLH-F-014): rendered views are primary evidence, a spec-derived feature
    checklist is required, and a reference image (when attached) must be
    compared visually.
    """

    review = build_quality_specialist_review(profile)
    judge = build_quality_specialist_judge(profile)
    for instructions in (review.instructions, judge.instructions):
        assert "feature_checklist" in instructions
        assert "reference image" in instructions.lower()
        assert "render" in instructions.lower()
        # Every spec feature category must be named so the reviewer knows what
        # to enumerate.
        for category in (
            "primitive",
            "subtracted",
            "added",
            "edge_treatment",
            "pattern",
            "thread",
        ):
            assert category in instructions.lower()
