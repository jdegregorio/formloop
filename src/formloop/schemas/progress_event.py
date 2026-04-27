"""Append-only progress event contract.

REQ: FLH-F-024, FLH-NF-006
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from ._common import SchemaModel, utcnow_iso


class ProgressEventKind(str, Enum):
    run_created = "run_created"
    spec_normalized = "spec_normalized"
    assumption_recorded = "assumption_recorded"
    research_topics_truncated = "research_topics_truncated"
    research_started = "research_started"
    research_completed = "research_completed"
    revision_started = "revision_started"
    cad_source_authored = "cad_source_authored"
    cad_validation_started = "cad_validation_started"
    cad_validation_failed = "cad_validation_failed"
    cad_validation_completed = "cad_validation_completed"
    revision_built = "revision_built"
    revision_rendered = "revision_rendered"
    revision_persisted = "revision_persisted"
    review_started = "review_started"
    review_completed = "review_completed"
    agent_tool_summary = "agent_tool_summary"
    breadcrumb = "breadcrumb"
    narration = "narration"
    delivered = "delivered"
    run_failed = "run_failed"


class ProgressEvent(SchemaModel):
    """One append-only progress event.

    ``message`` is human-friendly text. For ``kind == narration`` it is the
    LLM-written conversational status update (FLH-F-026); the orchestrator
    falls back to a static string when the Narrator agent fails. ``data``
    carries structured per-kind payload (e.g. ``phase``, ``signals``,
    ``narration_error``).
    """

    index: int = Field(ge=0, description="Zero-based ordinal within the run.")
    kind: ProgressEventKind
    ts: str = Field(default_factory=utcnow_iso)
    message: str = ""
    phase: str | None = Field(
        default=None,
        description=(
            "Coarse phase tag (plan/research/revision/review/final/failure). "
            "Always set for narration events; optional for milestone events."
        ),
    )
    narration_error: str | None = Field(
        default=None,
        description=(
            "Populated on narration events when the Narrator agent failed "
            "and the static fallback message was substituted (FLH-NF-010)."
        ),
    )
    data: dict[str, Any] = Field(default_factory=dict)
