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
    # Pydantic-level constraint — keeps narrator outputs from drifting into
    # walls of text that would break the in-place CLI rendering.
    schema = NarrationOutput.model_json_schema()
    assert schema["properties"]["text"]["maxLength"] == 400
