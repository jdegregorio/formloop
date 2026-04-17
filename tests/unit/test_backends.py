from __future__ import annotations

import pytest
from agents import OpenAIProvider
from agents.extensions.models.litellm_provider import LitellmProvider

from formloop.agents.backends import HeuristicBackend, OpenAIAgentsBackend
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


@pytest.mark.parametrize(
    ("profile_name", "provider_type", "expected_model"),
    [
        ("normal", OpenAIProvider, "gpt-5.4"),
        ("anthropic_normal", LitellmProvider, None),
    ],
)
def test_openai_agents_backend_configures_model_provider(
    configured_env,
    monkeypatch: pytest.MonkeyPatch,
    profile_name: str,
    provider_type: type,
    expected_model: str | None,
) -> None:
    backend = OpenAIAgentsBackend()
    profile = load_config(configured_env).profile(profile_name)
    captured: dict[str, object] = {}

    def fake_run_sync(agent, payload, run_config):
        captured["agent"] = agent
        captured["payload"] = payload
        captured["run_config"] = run_config

        class DummyResult:
            def final_output_as(self, output_type):
                if output_type is ManagerAssessment:
                    return ManagerAssessment.model_validate(
                        {
                            "normalized_spec": {
                                "summary": "ok",
                                "fit": [],
                                "form": ["block"],
                                "function": ["test"],
                                "constraints": [],
                                "blocking_gaps": [],
                                "key_dimensions": [],
                            },
                            "needs_clarification": False,
                            "clarification_reason": None,
                            "clarification_questions": [],
                            "assumptions": [],
                            "research_topics": [],
                        }
                    )
                raise AssertionError(f"Unexpected output type: {output_type}")

        return DummyResult()

    monkeypatch.setattr("formloop.agents.backends.Runner.run_sync", fake_run_sync)

    result = backend.structured_completion(
        role_name="Manager",
        instructions="test instructions",
        prompt="Create a block",
        output_type=ManagerAssessment,
        profile=profile,
    )

    assert result.needs_clarification is False
    run_config = captured["run_config"]
    assert isinstance(run_config.model_provider, provider_type)
    assert run_config.model == expected_model
