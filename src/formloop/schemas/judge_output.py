"""Persisted developer-eval judge output.

REQ: FLH-F-006, FLH-F-014, FLH-F-015
"""

from __future__ import annotations

from pydantic import Field

from ._common import SchemaModel
from .review_summary import ChecklistItem


class JudgeOutput(SchemaModel):
    """Quality Specialist judgment in eval mode."""

    case_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    pass_: bool = Field(alias="pass")
    dimension_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension 0..1 scores (e.g. geometric_accuracy, feature_presence).",
    )
    feature_checklist: list[ChecklistItem] = Field(
        default_factory=list,
        description="One row per spec feature; backs the dimension scores.",
    )
    rationale: str
    notes: list[str] = Field(default_factory=list)
