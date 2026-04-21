"""CAD Designer specialist.

REQ: FLH-F-003, FLH-F-028, FLH-F-029, FLH-D-004, FLH-D-009, FLH-D-020, FLH-D-026

Writes build123d Python (sandboxed to on-disk ``model.py`` + shelled-out
``cad build``), renders views, and returns a structured revision bundle with
a mandatory ``design_plan`` field laid out before authoring model.py.
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
from .cad_designer_plan import DesignPlan
from .common import (
    Agent,
    RunContext,
    RunContextWrapper,
    build_model_settings,
    function_tool,
    lenient_output,
)
from .knowledge import KnowledgeError, cheat_sheet_excerpt, search_topic


class CadRevisionResult(BaseModel):
    """Structured output from a CAD Designer turn."""

    design_plan: DesignPlan = Field(
        description=(
            "The short structured plan the designer committed to before "
            "authoring model.py. Required — emitted to the progress stream as "
            "a revision_planned event so the operator sees the approach."
        ),
    )
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


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

# Maximum characters to inline from the cheat sheet. Keeps the static portion
# of INSTRUCTIONS bounded (~3k tokens) while still giving the model an at-a-
# -glance reference. Deeper dives go through `build123d_lookup`.
_CHEAT_SHEET_MAX_CHARS = 8000


# Keyword → (import snippet, one-liner why-use) routing table. When the
# designer passes a topic that matches a trigger, the lookup response is
# prefixed with a paste-ready import block so the agent has a concrete entry
# point instead of having to hunt for it in prose.
_EXTERNAL_LIB_TRIGGERS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        ("thread", "threaded", "bolt", "screw", "fastener", "tapped", "pipe", "flange", "bearing"),
        (
            "# bd_warehouse.thread.* return build123d Parts directly — compose with +, -.\n"
            "from bd_warehouse.thread import IsoThread, TrapezoidalThread, AcmeThread, MetricTrapezoidalThread\n"
            "# Fasteners, bearings, pipes, flanges:\n"
            "from bd_warehouse import fastener, bearing, pipe, flange"
        ),
        "bd_warehouse generates correct helical thread geometry directly — do NOT hand-loft a helix. IsoThread(major_diameter, pitch, length, external=True, hand='right'|'left') is the standard entry point for metric threads.",
    ),
    (
        ("gear", "involute", "helical gear", "spur", "bevel", "rack", "pinion"),
        (
            "# py_gearworks builds a parametric gear and converts it to a build123d Part.\n"
            "import py_gearworks as pg\n"
            "# Entry points: pg.SpurGear, pg.HelicalGear, pg.BevelGear, pg.InvoluteGear.\n"
            "# Convert to build123d geometry with pg.GearBuilder(gear).generate_gear_stacks()\n"
            "# or use the GearToNurbs pipeline in conv_build123d.py."
        ),
        "py_gearworks already solves the involute flank + pitch/base circles + profile shift. Reuse it — call build123d_lookup again if you need the exact constructor signature.",
    ),
    (
        ("v-slot", "vslot", "aluminum extrusion", "aluminium extrusion", "t-slot", "20x20", "20x40", "40x40"),
        (
            "# bd_vslot ships OpenBuilds-style 20x20 profiles as build123d objects.\n"
            "from bd_vslot import VSlot2020Rail, VSlot2020RailProfile, VSlot2020EndCap, VSlot2020Wheel\n"
            "# e.g. VSlot2020Rail(length=300) yields a 300 mm 20x20 extrusion."
        ),
        "bd_vslot encodes the precise OpenBuilds 20x20 profile; don't sketch it by hand. Only 20x20 variants are shipped today — for other sizes fall back to stock build123d.",
    ),
    (
        ("beam", "i-beam", "upn", "ipn", "upe", "channel", "structural steel"),
        (
            "# bd_beams_and_bars encodes standard structural profiles (UPN, IPN, UPE).\n"
            "# REQUIRES PYTHON 3.13+ — if the current interpreter is 3.12, this import will fail.\n"
            "# import bd_beams_and_bars as bb"
        ),
        "bd_beams_and_bars encodes standard structural profiles; note the Py3.13+ requirement in open_questions and fall back to sketch+extrude if not available.",
    ),
)


def _external_lib_prelude(topic: str) -> str:
    """Return a paste-ready preamble for ``build123d_lookup`` when topic matches a trigger."""

    lowered = topic.lower()
    for triggers, snippet, rationale in _EXTERNAL_LIB_TRIGGERS:
        if any(t in lowered for t in triggers):
            return (
                f"# Routing: your topic matched an external-library trigger.\n"
                f"# {rationale}\n"
                f"# Paste-ready entry point:\n"
                f"```python\n{snippet}\n```\n\n"
            )
    return ""


def _build_instructions() -> str:
    """Compose the INSTRUCTIONS string, inlining a trimmed cheat sheet slice.

    Kept as a function (not a module-level constant evaluated at import time)
    so tests can monkey-patch the knowledge loader if needed.
    """
    cheat = cheat_sheet_excerpt(max_chars=_CHEAT_SHEET_MAX_CHARS)
    cheat_block = (
        f"\n\n## Quick reference — build123d cheat sheet (trimmed)\n\n{cheat}"
        if cheat
        else ""
    )
    return _INSTRUCTIONS_TEMPLATE + cheat_block


_INSTRUCTIONS_TEMPLATE = """You are the CAD Designer specialist in a CAD design harness.

You realize a design spec as a build123d Python module, then build, inspect,
and render it deterministically via the harness's CAD CLI tools.

## Step 1 — PLAN (required, before any write_model call)

Before you touch `write_model`, lay out a short `DesignPlan` in your head
(you'll return it as part of `CadRevisionResult.design_plan` at the end):

 - **paradigm** — pick `algebra` (`Part = Box(...) + Cylinder(...)`), `builder`
   (`with BuildPart() as p: ...`), or `mixed`. One sentence of rationale.
 - **primary_primitives** — the specific build123d constructs you expect to
   use (short names: `Box`, `Cylinder`, `fillet`, `extrude`, `mirror`, ...).
 - **external_libs_used** — list the short names of every ecosystem library
   you plan to import (`bd_warehouse`, `bd_vslot`, `py_gearworks`,
   `bd_beams_and_bars`). If one of the Step 2 LOOKUP triggers applies, this
   list should almost always be non-empty.
 - **decomposition** — 2–6 short bullets of the sub-parts / sub-operations
   and the order you'll assemble them.
 - **open_questions** — anything the spec didn't pin down that you had to
   assume (dimensions, orientation, material). Empty if nothing is unclear.

## Step 2 — LOOKUP (call it before you plan, when the spec hits a trigger)

You have a `build123d_lookup(topic)` tool that reaches into a curated local
knowledge pack: the 12 official Build123D doc pages PLUS inline pointers to
four external ecosystem libraries. The pack is already installed; importing
these libs at the top of `model.py` is free. You MUST call the lookup at
least once before PLAN if the spec mentions any of these triggers:

 - **threads / threaded / bolts / screws / fasteners / tapped holes / pipes /
   flanges / bearings** → `build123d_lookup("bd_warehouse thread")` or
   `build123d_lookup("bd_warehouse fastener")`. Use `bd_warehouse.thread.IsoThread`,
   `TrapezoidalThread`, `AcmeThread`, `bd_warehouse.fastener` classes, or
   `bd_warehouse.bearing`/`pipe`/`flange` modules — these produce correct
   helical geometry directly; do NOT hand-roll thread math.
 - **gear / gears / involute / helical / spur / bevel / rack / pinion** →
   `build123d_lookup("py_gearworks gear")`. Use `py_gearworks` generators —
   do NOT reconstruct involute tooth profiles by hand. The library already
   gets pitch circle, base circle, profile shift, and helix angle right.
 - **v-slot / aluminum extrusion / 20x20 / 20x40 / 40x40 T-slot** →
   `build123d_lookup("bd_vslot extrusion")`. Use `bd_vslot` profile classes.
 - **beam / UPN / IPN / UPE / channel / I-beam / structural steel** →
   `build123d_lookup("bd_beams_and_bars beam")`. Note in
   `open_questions` that `bd_beams_and_bars` needs Python 3.13+.

If none of those triggers apply, lookup is optional — use it whenever the
cheat-sheet excerpt below doesn't spell out the construct you need.

## Step 3..N — AUTHOR, BUILD, INSPECT, RENDER

Now author a build123d Python module that defines
`def build_model(params: dict, context: object)` returning a single solid.

Then, in order:
 - `write_model(source=...)` — persist the full source.
 - `build_model_cli()` — run `cad build`. If it errors, read the error,
   fix the Python, and retry up to 2 times.
 - `inspect_model()` — verify dimensions / volume / hole count against spec.
 - `render_model()` — produce views + sheet once the build is clean.

## Subprocess-exec boundary (IMPORTANT)

`model.py` is loaded by `cad build` in a **fresh Python interpreter**. All
imports MUST be at the top of the file. `build_model(params, context)` must
be self-contained — no reliance on harness state, no side effects, no I/O.

Example top-of-file:

```python
from build123d import Box, Cylinder, Align, Mode
from bd_warehouse.thread import IsoThread  # only if you chose bd_warehouse

def build_model(params, context):
    shaft = Cylinder(radius=3.0, height=50.0, align=Align.CENTER)
    return shaft
```

## When to reach outside build123d — prefer the specialized library

If the spec lands on one of the triggers above, the right answer is usually
to import the specialized library, not to hand-build the geometry. These
libraries encapsulate tricky math (involute flanks, thread helices, I-beam
fillets) that is easy to get subtly wrong from scratch.

 - `bd_warehouse` — threaded fasteners (`IsoThread`, `AcmeThread`,
   `TrapezoidalThread`), bearings, pipes, flanges, helical threaded holes.
   Prefer this over approximating threads with helical loft math.
 - `bd_vslot` — V-slot aluminum extrusion profiles (20×20, 20×40, 40×40, …).
   Prefer this over sketching the T-slot cross-section yourself.
 - `py_gearworks` — involute spur/helical gears, bevel gears, racks.
   Prefer this over computing involute points yourself.
 - `bd_beams_and_bars` — structural beams (UPN, IPN, UPE). Requires
   Python 3.13+ — if you choose this, note the version constraint in
   `open_questions`.

When a trigger doesn't apply (plain primitives, filleted plates, simple
profiles) stick with stock build123d — don't import a lib you won't use.
Populate `external_libs_used` with the short module name of every lib you
actually import in `model.py`; leave it empty otherwise.

## Rules

 - All measurements are millimeters.
 - Do NOT fabricate inspection numbers — only report dimensions that survived
   the `cad inspect` check.
 - Return a `CadRevisionResult` with `design_plan` populated, listing any
   residual risks, and recording key dimensions you believe the solid has.
"""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


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

    @function_tool
    async def build123d_lookup(
        ctx: RunContextWrapper[RunContext],  # noqa: ARG001 — required by SDK
        topic: str,
    ) -> str:
        """Look up a topic in the curated Build123D knowledge pack.

        Use this for on-demand reference when the cheat sheet inlined in your
        instructions doesn't cover something. The pack includes the official
        build123d docs (key concepts, objects catalog, operations, topology
        selection, builders, joints, assemblies, import/export, cheat sheet)
        plus curated pointers to external libraries (bd_warehouse, bd_vslot,
        py_gearworks, bd_beams_and_bars).

        Args:
            topic: A terse keyword phrase, or a slug from the pack
                (e.g. ``"threaded rod"``, ``"topology selection"``,
                ``"cheat_sheet"``).

        Returns:
            A short markdown excerpt (≤ ~1500 chars) of the best-matching
            page section, with a link to the full upstream source.
        """

        prelude = _external_lib_prelude(topic)
        try:
            body = search_topic(topic, max_chars=1500)
        except KnowledgeError as exc:  # pragma: no cover — pack is shipped
            return f"build123d_lookup unavailable: {exc}"
        return f"{prelude}{body}" if prelude else body

    return Agent[RunContext](
        name="cad_designer",
        instructions=_build_instructions(),
        model=profile.model,
        model_settings=build_model_settings(profile),
        tools=[
            write_model,
            build_model_cli,
            inspect_model,
            render_model,
            build123d_lookup,
        ],
        output_type=lenient_output(CadRevisionResult),
    )


__all__ = ["CadRevisionResult", "DesignPlan", "build_cad_designer"]
