"""Review summary contract (normal design review mode).

REQ: FLH-F-007, FLH-F-010
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from ._common import SchemaModel


class ReviewDecision(str, Enum):
    pass_ = "pass"
    revise = "revise"


class ChecklistCategory(str, Enum):
    primitive = "primitive"
    subtracted = "subtracted"
    added = "added"
    edge_treatment = "edge_treatment"
    pattern = "pattern"
    thread_gear_spline = "thread_gear_spline"
    other = "other"


class ChecklistMethod(str, Enum):
    visual = "visual"
    inspect = "inspect"
    both = "both"
    unverified = "unverified"


class ChecklistVerdict(str, Enum):
    pass_ = "pass"
    fail = "fail"
    unverified = "unverified"


class ChecklistItem(SchemaModel):
    """One row of the reviewer's spec-derived feature checklist.

    The reviewer enumerates every feature called out by the spec — overall
    primitive + dimensions, subtracted features, added features, edge
    treatments, patterns, and any thread / gear / spline features — and
    produces one ``ChecklistItem`` per feature with a verdict backed by either
    the rendered views, the inspect summary, or both.
    """

    feature: str = Field(description="Short label identifying the feature.")
    category: ChecklistCategory
    expected: str = Field(description="What the spec calls for, in the reviewer's words.")
    observed: str = Field(
        default="",
        description="What the reviewer actually saw in the renderings or inspect summary.",
    )
    method: ChecklistMethod
    verdict: ChecklistVerdict
    notes: str = ""


class ReviewSummary(SchemaModel):
    """Concise structured output of normal design review for one revision."""

    decision: ReviewDecision
    confidence: float = Field(ge=0.0, le=1.0)
    feature_checklist: list[ChecklistItem] = Field(
        default_factory=list,
        description="One row per spec feature; primary basis for the decision.",
    )
    key_findings: list[str] = Field(default_factory=list)
    suspect_or_missing_features: list[str] = Field(default_factory=list)
    suspect_dimensions_to_recheck: list[str] = Field(default_factory=list)
    reference_image_notes: str | None = Field(
        default=None,
        description="Narrative comparison of the rendered geometry to the "
        "reference image, when one was attached.",
    )
    revision_instructions: str = Field(
        default="",
        description="Concrete instructions for the CAD Designer's next attempt. "
        "Empty string when decision is pass.",
    )
