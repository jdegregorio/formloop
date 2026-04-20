"""Narrator agent constructs cleanly with the expected surface.

REQ: FLH-F-024, FLH-F-026, FLH-D-007, FLH-D-008, FLH-D-010, FLH-D-025
"""

from __future__ import annotations

from formloop.agents import (
    DEFAULT_NARRATOR_PROFILE,
    NarrationInput,
    NarrationOutput,
    build_narrator,
)
from formloop.config.profiles import Profile


def _underlying_type(agent):
    ot = agent.output_type
    return getattr(ot, "_output_type", getattr(ot, "output_type", ot))


def test_default_profile_is_lightweight() -> None:
    p = DEFAULT_NARRATOR_PROFILE
    assert p.model == "gpt-5.4-nano"
    assert p.reasoning == "low"


def test_narrator_constructs_with_default_profile() -> None:
    agent = build_narrator()
    assert agent.name == "narrator"
    assert agent.model == "gpt-5.4-nano"
    assert _underlying_type(agent) is NarrationOutput
    assert list(agent.tools) == []
    assert "First-person plural" in agent.instructions
    # FLH-D-025 — the agent is told never to leak identifiers.
    assert "internal identifiers" in agent.instructions


def test_narrator_accepts_profile_override() -> None:
    custom = Profile(name="bigger", model="gpt-5.4", reasoning="high")
    agent = build_narrator(custom)
    assert agent.model == "gpt-5.4"
    assert agent.model_settings.reasoning is not None
    assert agent.model_settings.reasoning.effort == "high"


def test_narration_input_round_trip() -> None:
    payload = NarrationInput(
        phase="revision",
        just_completed="ran the CAD designer",
        next_step="persist the revision",
        why="we want a baseline",
        signals={"attempt": 1, "build_ok": True},
    )
    js = payload.model_dump_json()
    restored = NarrationInput.model_validate_json(js)
    assert restored == payload


def test_narration_output_enforces_max_length() -> None:
    # Pydantic-level constraint — keeps narrator outputs bounded. Bumped
    # from 400 → 500 to accommodate the richer, run-specific narrations
    # the orchestrator now feeds via ``context`` (resolved ambiguities,
    # review findings, dimension callouts).
    schema = NarrationOutput.model_json_schema()
    assert schema["properties"]["text"]["maxLength"] == 500


def test_narration_input_accepts_context_payload() -> None:
    # Post-op-feedback: narrations need to weave in run-specific content,
    # so ``NarrationInput`` now carries a free-form ``context`` dict the
    # Narrator is told to quote from.
    payload = NarrationInput(
        phase="review",
        just_completed="finished the review",
        next_step="iterate on the design",
        why="",
        signals={"decision": "revise"},
        context={
            "key_findings": ["holes are 34mm instead of 35mm"],
            "decision": "revise",
        },
    )
    restored = NarrationInput.model_validate_json(payload.model_dump_json())
    assert restored.context["key_findings"] == ["holes are 34mm instead of 35mm"]
    # The agent instructions must explicitly tell the model to use context.
    from formloop.agents.narrator import INSTRUCTIONS

    assert "context" in INSTRUCTIONS.lower()
