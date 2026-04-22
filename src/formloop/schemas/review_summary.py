"""Review summary contract (normal design review mode).

REQ: FLH-F-007, FLH-F-010
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from ._common import SchemaModel


class ReviewDecision(str, Enum):
    pass_ = "pass"
    revise = "revise"


class ReviewSummary(SchemaModel):
    """Concise structured output of normal design review for one revision."""

    decision: ReviewDecision
    confidence: float = Field(ge=0.0, le=1.0)
    key_findings: list[str] = Field(default_factory=list)
    feature_checklist: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Flexible per-feature review checklist entries. Keep structure light-weight.",
    )
    suspect_or_missing_features: list[str] = Field(default_factory=list)
    suspect_dimensions_to_recheck: list[str] = Field(default_factory=list)
    reference_image_notes: str | None = None
    revision_instructions: str = Field(
        default="",
        description="Concrete instructions for the CAD Designer's next attempt. "
        "Empty string when decision is pass.",
    )
