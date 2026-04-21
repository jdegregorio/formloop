"""CAD Designer planning schema.

The Designer is required to lay out a short structured ``DesignPlan`` before
it starts authoring ``model.py`` — paradigm choice, the specific build123d
constructs it intends to use, a 2–6 bullet decomposition of the part, any
external-library reach, and open questions it couldn't answer from the spec.

Decision (from the feature plan): keep planning as a field on the existing
``CadRevisionResult`` — one LLM turn, one output, no extra round-trip. The
orchestrator unpacks the plan into a ``revision_planned`` progress event and
weaves paradigm + first decomposition bullet into the Narrator's context so
the live feed surfaces it.

REQ: FLH-F-028
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DesignParadigm = Literal["algebra", "builder", "mixed"]


class DesignPlan(BaseModel):
    """Structured plan the CAD Designer commits to before writing model.py."""

    paradigm: DesignParadigm = Field(
        description=(
            "build123d paradigm to use — 'algebra' for Part = Box(...) + "
            "Cylinder(...) style, 'builder' for `with BuildPart() as p: ...` "
            "stateful contexts, 'mixed' when one sub-part needs each."
        ),
    )
    paradigm_rationale: str = Field(
        min_length=1,
        max_length=240,
        description="One-sentence justification for the paradigm choice.",
    )
    primary_primitives: list[str] = Field(
        default_factory=list,
        max_length=16,
        description=(
            "Named build123d primitives/operations you plan to use (e.g. "
            "'Box', 'Cylinder', 'fillet', 'extrude', 'mirror'). Short names, "
            "no full signatures."
        ),
    )
    external_libs_used: list[str] = Field(
        default_factory=list,
        max_length=4,
        description=(
            "External libraries you plan to reach for — must be one of "
            "'bd_warehouse', 'bd_vslot', 'py_gearworks', 'bd_beams_and_bars'. "
            "Leave empty if stock build123d suffices (preferred)."
        ),
    )
    decomposition: list[str] = Field(
        min_length=1,
        max_length=8,
        description=(
            "2–6 short bullets describing the sub-operations / sub-parts and "
            "the order you'll assemble them. Each bullet ≤ 120 chars."
        ),
    )
    open_questions: list[str] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "Anything the spec didn't pin down that you had to assume — "
            "dimensions, orientation, material. Empty if nothing is unclear."
        ),
    )


__all__ = ["DesignParadigm", "DesignPlan"]
