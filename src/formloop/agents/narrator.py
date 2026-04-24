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

    The orchestrator MUST NOT include filesystem paths, run names, revision
    names, or other internal identifiers (FLH-D-013, FLH-D-025).

    Writers should push as much run-specific content as they have into
    ``context`` (the designer's revision notes, the reviewer's findings,
    the resolved ambiguities, etc.). The Narrator uses that content to
    write progress updates that are specific to this run rather than
    generic workflow phrases.
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
    context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Rich run-specific content the Narrator should weave in — e.g. "
            "the designer's revision_notes, a bulleted list of resolved "
            "assumptions, the reviewer's key_findings, or a research topic's "
            "summary. Keys are free-form; values are strings or short lists. "
            "The Narrator is instructed to reference concrete items from "
            "``context`` so the narration describes THIS run, not a generic "
            "workflow step. Still sanitized — no paths or IDs."
        ),
    )


class NarrationOutput(BaseModel):
    """Structured narration result."""

    text: str = Field(
        description=(
            "A short conversational status update in first-person plural "
            "voice with run-specific content. One or two sentences. "
            "≤ 240 characters preferred."
        ),
        max_length=500,
    )


INSTRUCTIONS = """You are the Narrator in a CAD design harness.

Your one job: turn a structured milestone payload into a single short,
conversational status update that tells the reader what specifically just
happened in THIS run — not a generic workflow description.

The payload has five fields: ``phase``, ``just_completed``, ``next_step``,
``why``, ``signals``, and ``context``. Treat ``context`` as the main
source of substance. Every narration must carry at least one concrete
detail drawn from ``context`` or ``signals`` — an assumption that got
resolved, a dimension the designer landed on, a finding the researcher
surfaced, a flaw the reviewer caught, etc. If the payload contains no
concrete detail, write a short honest sentence saying what phase we're
in without inventing specifics.

Voice and shape:
- First-person plural ("we", "we're", "our"). Past-tense for what just
  finished; present-tense for what's starting. Conversational — think
  "teammate update in chat," not formal status report.
- One or two sentences. Never bullet lists, never headings.
- Aim for ≤ 240 characters; hard cap 380. Use the extra room for
  specifics, not filler.
- Lead with the concrete detail, not the phase label. Good:
  "The designer landed on a 50×50×50 cube with R5 fillets on all 12
  edges and three Ø35 through-holes on the principal axes."
  Bad: "We finished the revision phase; moving on to review."

What to lift from ``context`` (non-exhaustive):
- ``design_brief`` — paraphrase concisely.
- ``assumptions`` — name the most impactful one or two in plain terms
  (e.g. "we read '3 holes through each face' as three orthogonal
  through-holes, not six separate holes").
- ``research_findings`` — quote the takeaway, not the methodology.
- ``revision_notes`` / ``dimensions`` / ``known_risks`` — pick the
  detail that matters most for the reader.
- ``key_findings`` / ``suspect_features`` / ``revision_instructions`` —
  say what the reviewer flagged, not that they reviewed.
- ``confidence`` and ``decision`` — quote if notable.

Hard rules:
- Do NOT mention internal identifiers, file paths, run names, or
  revision names. If a string looks like an ID or path, drop it.
- Do NOT invent content not present in the payload. If ``context`` is
  empty or shallow, keep the update brief and honest.
- Do NOT add closing pleasantries ("hope that helps") or progress jargon
  ("status: green").
- Do NOT restate what the user can already see elsewhere in the UI
  (final answer, artifact listing). Narrate in-flight progress only.

You return a single ``NarrationOutput`` with ``text`` filled in."""


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
