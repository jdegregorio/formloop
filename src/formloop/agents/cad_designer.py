"""CAD Designer agent definition."""

from __future__ import annotations

from agents import Agent

from ..models import CadDesignOutput
from .common import HarnessAgentContext, reasoning_settings


def build_cad_designer_agent(*, model: str, reasoning: str) -> Agent[HarnessAgentContext]:
    # Req: FLH-F-003, FLH-D-010, FLH-D-011
    instructions = """
You are the CAD Designer for Formloop.

Return only structured output for one deterministic build123d model candidate.
Write complete Python source code that defines:

    def build_model(params, context):
        ...

Rules:
- Use build123d as the primary modeling backend.
- Target a single solid or compound appropriate for cad-cli build.
- Keep code deterministic and readable.
- Do not use file I/O, networking, subprocesses, environment access,
  or imports outside build123d/math/typing.
- Prefer conservative build123d APIs that are known to work broadly.
- Do not rely on convenience kwargs such as `centered=...` on primitives;
  instead use explicit `Pos(...)`, `Location(...)`, or boolean placement.
- Do not pass placement kwargs such as `pos=` to primitives.
- Preferred pattern:
  - `shape = Pos(x, y, z) * Box(width, depth, height)`
  - `shape = shape - (Pos(x, y, z) * Cylinder(radius, height))`
- If a feature needs rotation, always pass both axis and angle, for example:
  - `cyl = cyl.rotate(Axis.Y, 90)`
- Prefer direct dimensions from the spec and assumptions.
- If previous review feedback exists, revise the model to address it.
- The source must be ready to execute by cad-cli without additional editing.
"""
    return Agent[HarnessAgentContext](
        name="CAD Designer",
        handoff_description="Produces deterministic build123d source for the candidate revision.",
        instructions=instructions,
        model=model,
        model_settings=reasoning_settings(reasoning),
        output_type=CadDesignOutput,
    )
