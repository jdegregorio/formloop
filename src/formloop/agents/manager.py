"""Manager (hub) agent.

REQ: FLH-F-002, FLH-F-004, FLH-F-017, FLH-F-019, FLH-F-020, FLH-D-007
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from .common import Agent, build_model_settings, lenient_output


class AssumptionProposal(BaseModel):
    topic: str = Field(description="Short label for what the assumption is about.")
    assumption: str = Field(description="The stated value or choice we are assuming.")


class ManagerPlan(BaseModel):
    """Structured plan the manager produces at the start of a run (FLH-F-001)."""

    normalized_spec: dict = Field(
        description=(
            "Machine-readable design spec. Must include dimensions in mm, "
            "counts of named features, and any tolerances."
        )
    )
    assumptions: list[AssumptionProposal] = Field(
        default_factory=list,
        description="Assumptions made when the user input was ambiguous (FLH-F-020).",
    )
    research_topics: list[str] = Field(
        default_factory=list,
        description=(
            "Narrow, single-answer research questions. Empty if no external "
            "references are needed (FLH-F-016, FLH-F-018)."
        ),
    )
    design_brief: str = Field(
        description="Short natural-language brief the CAD designer will act on."
    )


class ManagerFinalAnswer(BaseModel):
    """Final user-facing synthesis (FLH-F-002, FLH-F-019)."""

    text: str = Field(description="Plain-text summary for the operator.")
    delivered_revision_name: str | None = None


PLAN_INSTRUCTIONS = """You are the Manager of a CAD design harness.

You own the user's request end-to-end. Your first job, on the initial turn of a
run, is to produce a ``ManagerPlan`` that normalizes the (possibly vague) user
prompt into a concrete design spec and a short design brief for the CAD designer.

Rules:
- Emit all dimensions in millimeters. If the user used inches or ambiguous
  units, convert and record the conversion as an assumption.
- Populate ``normalized_spec`` with keys like ``kind``, ``overall_dimensions_mm``
  (dict with width/depth/height or radius/length as appropriate), ``features``
  (list of objects with type + dimensions + count + positions), and
  ``tolerances``.
- If the user under-specifies a value (e.g. "a plate with holes" with no hole
  count), pick a sensible minimum and record it as an assumption. Prefer simple
  round values.
- ``research_topics`` should be EMPTY when the spec is self-contained. Include a
  topic only when an external fact (a standard, a material property, a
  manufacturing norm) is needed for a defensible design.
- ``design_brief`` is 2-4 sentences: the shape, its key dimensions, and which
  features matter most.
- Do not write CAD code or reference filesystem identifiers here."""


FINAL_INSTRUCTIONS = """You are the Manager of a CAD design harness, producing
the FINAL answer after the revision loop has terminated.

Inputs you receive in the user message:
- The normalized spec.
- A summary of each revision attempted and the final review decision.
- The delivered revision's dimensions and any remaining risks.

Produce a ``ManagerFinalAnswer`` whose ``text``:
- Opens with a one-sentence direct answer to the user's original request.
- Lists the delivered dimensions in a compact way.
- Calls out any known risks or remaining uncertainties plainly.
- Mentions the revision count and where the artifacts live (by logical name, not
  full path).
Set ``delivered_revision_name`` to the rev-NNN label that was delivered."""


def build_manager_plan(profile: Profile) -> Agent[None]:
    """Manager configured for the initial planning turn."""

    return Agent(
        name="manager_planner",
        instructions=PLAN_INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        output_type=lenient_output(ManagerPlan),
    )


def build_manager_final(profile: Profile) -> Agent[None]:
    """Manager configured for the final-answer turn."""

    return Agent(
        name="manager_final",
        instructions=FINAL_INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        output_type=lenient_output(ManagerFinalAnswer),
    )


__all__ = [
    "AssumptionProposal",
    "ManagerFinalAnswer",
    "ManagerPlan",
    "build_manager_final",
    "build_manager_plan",
]
