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
    research_started = "research_started"
    research_completed = "research_completed"
    revision_started = "revision_started"
    revision_built = "revision_built"
    revision_rendered = "revision_rendered"
    revision_persisted = "revision_persisted"
    review_started = "review_started"
    review_completed = "review_completed"
    breadcrumb = "breadcrumb"
    delivered = "delivered"
    run_failed = "run_failed"


class ProgressEvent(SchemaModel):
    """One append-only progress event.

    ``message`` is human-friendly breadcrumb text (may be LLM-generated for
    ``kind == breadcrumb``). ``data`` carries structured per-kind payload.
    """

    index: int = Field(ge=0, description="Zero-based ordinal within the run.")
    kind: ProgressEventKind
    ts: str = Field(default_factory=utcnow_iso)
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
