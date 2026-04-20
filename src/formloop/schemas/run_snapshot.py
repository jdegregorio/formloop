"""Polling-friendly materialized view of run state.

REQ: FLH-F-024, FLH-F-025, FLH-NF-006
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ._common import SchemaModel, utcnow_iso
from .review_summary import ReviewDecision


class SnapshotArtifacts(SchemaModel):
    step_path: str | None = None
    glb_path: str | None = None
    render_sheet_path: str | None = None
    view_paths: list[str] = Field(default_factory=list)


class RunSnapshot(SchemaModel):
    """Materialized, polling-friendly view of current run state."""

    run_id: str
    run_name: str
    status: str
    generated_at: str = Field(default_factory=utcnow_iso)

    current_spec: dict[str, Any] = Field(default_factory=dict)
    current_revision_name: str | None = None
    revisions: list[str] = Field(default_factory=list)

    latest_review_decision: ReviewDecision | None = None
    latest_review_summary_path: str | None = None

    artifacts: SnapshotArtifacts = Field(default_factory=SnapshotArtifacts)
    last_event_index: int = Field(default=-1, ge=-1)
    last_event_kind: str | None = None
    last_message: str | None = None

    # Latest LLM-written progress narration — what the UI / CLI surfaces as
    # the live "reasoning trace" line under the latest user message
    # (FLH-F-024, FLH-F-026).
    latest_narration: str | None = None
    latest_narration_phase: str | None = None
    latest_narration_index: int | None = Field(default=None, ge=0)
