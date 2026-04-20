"""Revision contract.

REQ: FLH-F-009, FLH-F-022, FLH-D-024
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from ._common import SchemaModel, utcnow_iso


class RevisionTrigger(str, Enum):
    initial = "initial"
    review_revise = "review_revise"
    manual = "manual"


class Revision(SchemaModel):
    """One persisted candidate iteration inside a run (FLH-F-022)."""

    revision_id: str
    revision_name: str = Field(description="Human-readable sequential like rev-001.")
    ordinal: int = Field(ge=1)
    created_at: str = Field(default_factory=utcnow_iso)
    trigger: RevisionTrigger

    spec_snapshot: dict[str, Any] = Field(default_factory=dict)
    designer_notes: str | None = None
    known_risks: list[str] = Field(default_factory=list)

    artifact_manifest_path: str
    review_summary_path: str | None = None
