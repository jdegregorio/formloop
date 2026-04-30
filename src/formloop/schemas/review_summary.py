"""Review summary contract (normal design review mode).

REQ: FLH-F-007, FLH-F-010
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from ._common import SchemaModel


class ReviewDecision(str, Enum):
    pass_ = "pass"
    revise = "revise"


class ReviewOutcome(str, Enum):
    revise = "revise"
    watch = "watch"
    pass_ = "pass"


class ReviewSummary(SchemaModel):
    """Concise structured output of normal design review for one revision."""

    schema_version: Literal[2] = 2
    decision: ReviewDecision
    outcome: ReviewOutcome
    summary: str = Field(
        min_length=1,
        description="One concise user-facing sentence summarizing what the review found.",
    )
    next_step: str = Field(
        min_length=1,
        description="One concise user-facing sentence describing what should happen next.",
    )
    key_findings: list[str] = Field(default_factory=list)
    revision_instructions: str = Field(
        default="",
        description="Concrete instructions for the CAD Designer's next attempt. "
        "Empty string when decision is pass.",
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_v1(cls, data: Any) -> Any:
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            return data

        decision = data.get("decision")
        outcome = "pass" if decision == "pass" else "revise"
        key_findings = list(data.get("key_findings") or [])
        revision_instructions = str(data.get("revision_instructions") or "")
        suspect_features = list(data.get("suspect_or_missing_features") or [])
        suspect_dimensions = list(data.get("suspect_dimensions_to_recheck") or [])
        reference_notes = data.get("reference_image_notes")

        summary = (
            first_text(key_findings)
            or first_text(suspect_features)
            or first_text(suspect_dimensions)
            or revision_instructions
            or (
                "Review accepted this revision."
                if decision == "pass"
                else "Review requested changes."
            )
        )
        next_step = (
            "Deliver this design."
            if decision == "pass"
            else revision_instructions or "Revise the design using the review findings."
        )
        migrated_findings = [*key_findings, *suspect_features, *suspect_dimensions]
        if reference_notes:
            migrated_findings.append(str(reference_notes))

        return {
            "schema_version": 2,
            "decision": decision,
            "outcome": outcome,
            "summary": summary,
            "next_step": next_step,
            "key_findings": migrated_findings,
            "revision_instructions": revision_instructions,
        }


def first_text(items: list[Any]) -> str:
    for item in items:
        text = str(item).strip()
        if text:
            return text
    return ""
