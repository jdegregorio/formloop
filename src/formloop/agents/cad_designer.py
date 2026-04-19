"""CAD Designer specialist.

REQ: FLH-F-003, FLH-D-004, FLH-D-009, FLH-D-020

Writes build123d Python (sandboxed to on-disk ``model.py`` + shelled-out
``cad build``), renders views, and returns a structured revision bundle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from ..runtime.cad_cli import (
    CadBuildResult,
    CadInspectResult,
    CadRenderResult,
    cad_build,
    cad_inspect_summary,
    cad_render,
)
from ..runtime.constrained_python import write_model_source
from .common import (
    Agent,
    RunContext,
    RunContextWrapper,
    build_model_settings,
    function_tool,
    lenient_output,
)


class CadRevisionResult(BaseModel):
    """Structured output from a CAD Designer turn."""

    model_py_written: bool = Field(description="True if the designer persisted model.py.")
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
            "Key nominal dimensions in mm — values may be numbers or short lists "
            "(e.g. coordinates). Keys like width, depth, height, hole_diameter."
        ),
    )
    build_errors: list[str] = Field(default_factory=list)


INSTRUCTIONS = """You are the CAD Designer specialist in a CAD design harness.

You realize a current design spec as a build123d Python module, then build,
inspect, and render it deterministically via the harness's CAD CLI tools.

Workflow every turn:
1. Read the spec + any prior review instructions provided in the user message.
2. Author a build123d Python module that defines
   ``def build_model(params: dict, context: object)`` and returns a single solid.
   - Default values inside ``build_model`` should match the spec exactly so that
     ``cad build`` succeeds with no overrides.
   - Use only ``build123d`` primitives: Box, Cylinder, Sphere, Cone, Pos, Rot,
     boolean union (+), difference (-), intersection (&). Avoid exotic CAD.
   - Keep the source small and readable — the goal is a correct minimum solid.
3. Call ``write_model`` with the full source text.
4. Call ``build_model_cli`` to run ``cad build``. If it errors, read the error,
   fix the Python, and retry up to 2 times.
5. Call ``inspect_model`` to verify dimensions/volume/hole-count against the spec.
6. Call ``render_model`` once the build is clean.
7. Return a ``CadRevisionResult`` summarizing what you did, listing any residual
   risks, and recording the key dimensions you believe the solid has.

Rules:
- Do NOT import build123d constructs you are unsure about; stick to the allowed
  list above unless the spec truly requires more.
- All measurements are millimeters.
- Do not fabricate inspection numbers — only report dimensions that survived the
  ``cad inspect`` check."""


def build_cad_designer(profile: Profile) -> Agent[RunContext]:
    @function_tool
    async def write_model(ctx: RunContextWrapper[RunContext], source: str) -> str:
        """Persist the provided build123d source text to the run's inputs/model.py.

        Args:
            source: Full Python source defining ``build_model(params, context)``.

        Returns:
            Relative path label (not a filesystem identifier) confirming write.
        """

        run_ctx = ctx.context
        path = write_model_source(run_ctx.inputs_dir, source, filename="model.py")
        # Only surface a non-identifying confirmation back to the model.
        return f"model.py written ({path.stat().st_size} bytes)"

    @function_tool
    async def build_model_cli(
        ctx: RunContextWrapper[RunContext],
    ) -> dict:
        """Run ``cad build`` on the current model.py; returns the build summary."""

        run_ctx = ctx.context
        model_path = run_ctx.inputs_dir / "model.py"
        if not model_path.is_file():
            return {"status": "error", "detail": "model.py has not been written yet"}
        try:
            result: CadBuildResult = cad_build(
                model_path=model_path,
                output_dir=run_ctx.run_root / "_work" / "build",
            )
        except Exception as exc:  # subprocess/CliError bubble
            return {"status": "error", "detail": str(exc)[:2000]}
        run_ctx.notes["last_build"] = result.model_dump()
        return {
            "status": result.status,
            "volume_mm3": result.volume,
            "bounding_box": result.bounding_box.model_dump(),
        }

    @function_tool
    async def inspect_model(
        ctx: RunContextWrapper[RunContext],
    ) -> dict:
        """Inspect the most recently built STEP — returns bbox/volume/holes summary."""

        run_ctx = ctx.context
        last = run_ctx.notes.get("last_build")
        if not last:
            return {"status": "error", "detail": "no successful build yet"}
        step_path = Path(last["output_dir"]) / "model.step"
        try:
            summary: CadInspectResult = cad_inspect_summary(step_path)
        except Exception as exc:
            return {"status": "error", "detail": str(exc)[:2000]}
        run_ctx.notes["last_inspect"] = summary.model_dump()
        return {"status": summary.status, "mode": summary.mode, "data": summary.data}

    @function_tool
    async def render_model(
        ctx: RunContextWrapper[RunContext],
    ) -> dict:
        """Render views + sheet for the current build."""

        run_ctx = ctx.context
        last = run_ctx.notes.get("last_build")
        if not last:
            return {"status": "error", "detail": "no successful build yet"}
        glb_path = Path(last["output_dir"]) / "model.glb"
        try:
            result: CadRenderResult = cad_render(
                glb_path=glb_path,
                output_dir=run_ctx.run_root / "_work" / "render",
            )
        except Exception as exc:
            return {"status": "error", "detail": str(exc)[:2000]}
        run_ctx.notes["last_render"] = result.model_dump()
        views = [p.name for p in result.view_paths() if p.is_file()]
        return {"status": result.status, "views": views, "sheet": "sheet.png"}

    return Agent[RunContext](
        name="cad_designer",
        instructions=INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        tools=[write_model, build_model_cli, inspect_model, render_model],
        output_type=lenient_output(CadRevisionResult),
    )


__all__ = ["CadRevisionResult", "build_cad_designer"]
