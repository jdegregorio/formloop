from __future__ import annotations

from formloop.agents.backends import HeuristicBackend
from formloop.agents.contracts import ManagerAssessment, ReviewOutput
from formloop.config import load_config


def test_manager_clarifies_on_critical_gap(configured_env) -> None:
    backend = HeuristicBackend()
    profile = load_config(configured_env).profile("normal")
    result = backend.structured_completion(
        role_name="Manager",
        instructions="",
        prompt="Create some part for a thing with exact fit.",
        output_type=ManagerAssessment,
        profile=profile,
    )
    assert result.needs_clarification is True
    assert result.clarification_questions


def test_review_reference_note_only_when_true(configured_env) -> None:
    backend = HeuristicBackend()
    profile = load_config(configured_env).profile("normal")
    result = backend.structured_completion(
        role_name="Review Specialist",
        instructions="",
        prompt="Measurements: {} Reference image present: False",
        output_type=ReviewOutput,
        profile=profile,
    )
    assert result.summary.reference_image_notes == []

