"""Manager (hub) agent.

REQ: FLH-F-002, FLH-F-004, FLH-F-017, FLH-F-019, FLH-F-020, FLH-D-007
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from .common import Agent, build_model_settings, lenient_output


class AssumptionProposal(BaseModel):
    topic: str = Field(description="Short label for what the assumption is about.")
    assumption: str = Field(description="The stated value or choice we are assuming.")


class NormalizedSpec(BaseModel):
    """Structured, stable spec contract shared across the run."""

    name: str = Field(description="Short descriptive name for the component/assembly.")
    type: Literal["component", "assembly"] = Field(
        description="Whether this is a single component or an assembly."
    )
    units: str = Field(
        default="mm",
        description="Canonical units for dimensions. Prefer 'mm'.",
    )
    design_intent: str = Field(
        description="High-level functional/design intent summary for the model."
    )
    features: list[str] = Field(
        default_factory=list,
        description="List of meaningful geometric/features requirements.",
    )
    interfaces: list[str] = Field(
        default_factory=list,
        description="Interface requirements and mating/connection considerations.",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Hard constraints that must be satisfied.",
    )
    preferences: list[str] = Field(
        default_factory=list,
        description="Soft preferences and flexible options.",
    )
    manufacturing_method: str | None = Field(
        default=None,
        description="Preferred manufacturing method if specified or inferred.",
    )
    key_dimension_parameters: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Parameterized named dimensions (mm) that should align with model.py "
            "variables for later manual adjustment."
        ),
    )


class ManagerPlan(BaseModel):
    """Structured plan the manager produces at the start of a run (FLH-F-001)."""

    normalized_spec: NormalizedSpec = Field(
        description=("Machine-readable design spec using the structured NormalizedSpec contract.")
    )
    assumptions: list[AssumptionProposal] = Field(
        default_factory=list,
        description="Assumptions made when the user input was ambiguous (FLH-F-020).",
    )
    research_topics: list[str] = Field(
        default_factory=list,
        description=(
            "Focused research queries. These can cover external engineering facts "
            "and/or Build123D implementation methods when modeling strategy is "
            "non-obvious (FLH-F-016, FLH-F-018)."
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
- Populate ``normalized_spec`` with this exact high-level structure:
  - ``name``: short descriptive component/assembly name.
  - ``type``: ``component`` or ``assembly``.
  - ``units``: canonical units (prefer ``mm``).
  - ``design_intent``: concise high-level intent.
  - ``features``: list of key feature descriptions.
  - ``interfaces``: key interface/mating requirements.
  - ``constraints``: hard requirements.
  - ``preferences``: softer preferences/flexible dimensions.
  - ``manufacturing_method``: optional manufacturing preference.
  - ``key_dimension_parameters``: object of named numeric dimensions in mm
    (flat name/value map intended to line up with model.py variables).
- If the user under-specifies a value (e.g. "a plate with holes" with no hole
  count), pick a sensible minimum and record it as an assumption. Prefer simple
  round values.
- ``research_topics`` should be EMPTY only when the spec is fully self-contained
  and the CAD implementation approach is straightforward.
- Include research topics for BOTH:
  1) external facts (standards, material properties, manufacturing norms), and
  2) Build123D modeling-method questions (e.g. "how to build X feature with
     Build123D and available helper libraries").
- You do not need to classify topic types. A single mixed list is expected.
- ``design_brief`` is 2-4 sentences: the shape, its key dimensions, and which
  features matter most.
- Do not write CAD code or reference filesystem identifiers here."""


FINAL_INSTRUCTIONS = """You are the Manager of a CAD design harness, producing
the FINAL answer after the revision loop has terminated.

Inputs you receive in the user message:
- The normalized spec.
- A summary of each revision attempted and the final review decision.
- The delivered revision's dimensions and any remaining risks.
- Whether the latest review accepted the revision, or whether max revisions
  were exhausted with unresolved review feedback.

Produce a ``ManagerFinalAnswer`` whose ``text`` reads as a clean, user-facing
summary written in plain prose. Required structure:
- Opens with a one-sentence direct answer to the user's original request,
  written naturally — confirm what was delivered only when review accepted it.
  If max revisions were exhausted or latest review is revise, say the latest
  candidate is not accepted yet and summarize the remaining blocker.
- Lists the delivered dimensions in a compact way.
- Calls out any known risks or remaining uncertainties plainly.
- If the run did not pass review, avoid saying it is complete/successful.
- May briefly mention how many revision attempts were made if it adds
  meaningful context (e.g. "after one pass" or "after two iterations").

Strict rules for ``text``:
- DO NOT include the rev-NNN identifier, the run name, filesystem paths, or
  any other internal harness bookkeeping. The CLI / UI surfaces those
  separately. The reader of ``text`` should not need to know how revisions
  are named internally.
- Write in natural prose. Section labels and bullet lists are fine when
  they help scan dimensions or risks (e.g. "Delivered dimensions:" with a
  short bullet list), but keep the framing crisp and avoid restating things
  the surrounding UI already shows.

Set ``delivered_revision_name`` to the rev-NNN label that was delivered —
this is for the harness, not the user."""


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
    "NormalizedSpec",
    "build_manager_final",
    "build_manager_plan",
]
