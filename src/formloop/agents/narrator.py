"""Narrator specialist — converts orchestration milestones into prose.

REQ: FLH-F-024, FLH-F-026, FLH-D-007, FLH-D-008, FLH-D-010, FLH-D-025

The Narrator is a lightweight agent that turns a sanitized milestone
payload into a single short conversational status update. It runs on its
own dedicated cheap profile so the run's main profile can stay heavyweight
without paying nano costs to narrate, and it never sees raw filesystem
paths or internal identifiers (FLH-D-025).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from .common import Agent, build_model_settings, lenient_output


# Default profile for the Narrator. Pinned to a cheap reasoning model so
# the run's main profile can be heavyweight without inflating narration
# cost. Overridable for tests / future reconfiguration.
DEFAULT_NARRATOR_PROFILE = Profile(
    name="narrator",
    model="gpt-5.4-nano",
    reasoning="low",
    description="Lightweight progress narrator (FLH-F-026).",
)


class NarrationInput(BaseModel):
    """Sanitized milestone payload handed to the Narrator.

    Only conceptual fields — phase tag, what just happened, what's next,
    and a small bag of sanitized signals (numbers / short strings). The
    orchestrator MUST NOT include filesystem paths, run names, revision
    names, or other internal identifiers (FLH-D-013, FLH-D-025).
    """

    phase: str = Field(description="Coarse phase tag, e.g. plan/research/revision/review/final.")
    just_completed: str = Field(
        default="",
        description="What the harness just finished, as a short factual phrase.",
    )
    next_step: str = Field(
        default="",
        description="What the harness is about to do next, as a short factual phrase.",
    )
    why: str = Field(
        default="",
        description="Optional one-clause rationale; leave empty when not informative.",
    )
    signals: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Small sanitized key-value bag of useful numbers or labels (e.g. "
            "{'attempt': 2, 'decision': 'revise'}). No paths, no UUIDs."
        ),
    )


class NarrationOutput(BaseModel):
    """Structured narration result."""

    text: str = Field(
        description=(
            "One short conversational sentence (rarely two). First-person "
            "plural voice, present-tense for what is starting, past-tense "
            "for what just finished. ≤ 280 characters."
        ),
        max_length=400,
    )


INSTRUCTIONS = """You are the Narrator in a CAD design harness.

Your one job: turn a structured milestone payload into a single short,
conversational status update — the kind of message an engineer would type
into a chat to keep a teammate in the loop.

Voice and shape:
- First-person plural ("we", "we're", "our"). Present tense for what is
  starting; past tense for what just finished. Conversational, not formal.
- One sentence is almost always right. Two sentences only if "why" adds
  real signal. Never bullet lists, never headings.
- Aim for ≤ 200 characters; hard cap 280.
- Mention the "why" only when it is informative — e.g. "because the
  reviewer flagged the hole spacing." Skip it if it would just restate
  the obvious.

Hard rules:
- Do NOT mention internal identifiers, file paths, run names, or revision
  names. The payload is already sanitized; if a string looks like an ID
  or path, drop it.
- Do NOT speculate beyond the payload. Stick to what's there.
- Do NOT add closing pleasantries ("hope that helps") or progress jargon
  ("status: green").
- Numbers are useful — quote dimensions, attempt counts, confidence values
  when they're in `signals`.

You return a single ``NarrationOutput`` with the ``text`` field filled in."""


def build_narrator(profile: Profile | None = None) -> Agent[None]:
    """Construct the Narrator agent.

    Defaults to ``DEFAULT_NARRATOR_PROFILE`` so callers don't have to
    decide. Tests and special configurations may pass an explicit profile.
    """

    p = profile or DEFAULT_NARRATOR_PROFILE
    return Agent(
        name="narrator",
        instructions=INSTRUCTIONS,
        model=p.model,
        model_settings=build_model_settings(p),
        tools=[],
        output_type=lenient_output(NarrationOutput),
    )


__all__ = [
    "DEFAULT_NARRATOR_PROFILE",
    "NarrationInput",
    "NarrationOutput",
    "build_narrator",
]
