"""CAD Designer specialist.

REQ: FLH-F-003, FLH-D-004, FLH-D-009, FLH-D-020

Authors build123d Python source only. The harness owns deterministic writing,
building, inspection, rendering, and retry feedback so ``cad-cli`` execution is
bounded and inspectable outside the model loop.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from .build123d_libraries import available_build123d_libraries_text
from .common import Agent, RunContext, build_model_settings, lenient_output


class CadSourceResult(BaseModel):
    """Source-only payload authored by the CAD Designer.

    The harness writes ``source`` to ``model.py`` and runs all deterministic
    ``cad-cli`` commands. The optional self-report fields help review and
    debugging, but they are never treated as authoritative geometry evidence.
    """

    source: str = Field(
        min_length=1,
        description=(
            "Full Python source for model.py. It must define "
            "build_model(params: dict, context: object) and return one solid."
        ),
    )
    revision_notes: str = Field(
        description="Short narrative of the CAD approach and any tradeoffs."
    )
    known_risks: list[str] = Field(default_factory=list)
    intended_features: list[str] = Field(
        default_factory=list,
        description="Feature checklist the source is intended to satisfy.",
    )
    self_reported_dimensions: dict[str, Any] = Field(
        default_factory=dict,
        description="Designer-estimated nominal dimensions in mm; not authoritative.",
    )


class CadRevisionResult(BaseModel):
    """Harness-derived summary for a validated CAD revision attempt."""

    build_ok: bool
    inspect_ok: bool
    render_ok: bool
    revision_notes: str = Field(
        description="Short narrative of the approach taken and any tradeoffs."
    )
    known_risks: list[str] = Field(default_factory=list)
    dimensions: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Key nominal dimensions in mm. Harness inspect data is authoritative; "
            "self-reported dimensions are only advisory."
        ),
    )
    build_errors: list[str] = Field(default_factory=list)


INSTRUCTIONS = """You are the CAD Designer specialist in a CAD design harness.

You author exactly one build123d Python module. The harness will write your
source to model.py, then run cad build, cad inspect summary, and cad render.
You do not have CAD CLI tools in this phase; return source only.

Workflow every turn:
1. Read the spec + any prior review instructions provided in the user message.
2. If the message contains CAD_VALIDATION_FAILURE_FEEDBACK, repair the source
   specifically against that failing command/error before making broader changes.
3. Author a build123d Python module that defines
   ``def build_model(params: dict, context: object)`` and returns a single solid.
   - Default values inside ``build_model`` should match the spec exactly so that
     ``cad build`` succeeds with no overrides.
   - Prefer clear build123d primitives first (Box, Cylinder, Sphere, Cone, Pos,
     Rot, boolean union (+), difference (-), intersection (&)).
   - You may also use these installed Build123D ecosystem libraries when they
     are the best fit: """
INSTRUCTIONS += available_build123d_libraries_text()
INSTRUCTIONS += """
     (e.g. fasteners, beams/bars, V-slot components, gear generation).
   - Keep imports explicit and minimal; do not pull in uninstalled libraries.
   - Keep the source small and readable — the goal is a correct minimum solid.
   - For arbitrary 2D polygon tooth profiles, prefer ``Face(Wire.make_polygon(...))``.
     Do not call ``Polyline`` directly inside ``BuildSketch``; in build123d it is a
     line-builder operation and will fail in sketch context.
4. Return a ``CadSourceResult`` containing the complete source, revision notes,
   known risks, intended features, and any self-reported nominal dimensions.

Rules:
- Do NOT import CAD constructs you are unsure about.
- If a requested feature maps directly to an installed part library/helper,
  prefer that library over hand-rolling fragile geometry.
- All measurements are millimeters.
- Do not claim build, inspect, or render success. The harness will provide the
  authoritative validation result.
- ``source`` must be executable Python text, not Markdown and not a patch."""


def build_cad_designer(profile: Profile) -> Agent[RunContext]:
    return Agent[RunContext](
        name="cad_designer",
        instructions=INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        tools=[],
        output_type=lenient_output(CadSourceResult),
    )


__all__ = ["CadRevisionResult", "CadSourceResult", "build_cad_designer"]
