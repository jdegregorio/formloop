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
from .common import Agent, RunContext, build_model_settings, lenient_output

AVAILABLE_BUILD123D_LIBRARIES: tuple[str, ...] = (
    "bd_warehouse",
    "py_gearworks",
)


def _available_libraries_text() -> str:
    return ", ".join(AVAILABLE_BUILD123D_LIBRARIES)


BUILD123D_CHEAT_SHEET = """\
Build123D + extension cheat sheet (required args first, optional args follow):

Core primitives (build123d)
| Object        | Required args                          | Optional args                                    | Notes |
|---------------|----------------------------------------|--------------------------------------------------|-------|
| `Box`         | `length, width, height`                | `rotation=(0,0,0)`, `align=(C,C,C)`, `mode`      | Centered by default. |
| `Cylinder`    | `radius, height`                       | `arc_size=360`, `rotation`, `align`, `mode`      | Axis is +Z. |
| `Cone`        | `bottom_radius, top_radius, height`    | `arc_size=360`, `rotation`, `align`, `mode`      | Either radius may be 0. |
| `Sphere`      | `radius`                               | `arc_size1=-90`, `arc_size2=90`, `arc_size3=360` | |
| `Torus`       | `major_radius, minor_radius`           | `minor_start_angle`, `minor_end_angle`           | |
| `Wedge`       | `xsize, ysize, zsize, xmin, zmin, xmax, zmax` | `rotation`, `align`, `mode`               | Use only when prism slope is needed. |

Sketches / 2D (build123d)
| Object              | Required args                  | Optional args                            | Notes |
|---------------------|--------------------------------|------------------------------------------|-------|
| `Rectangle`         | `width, height`                | `rotation=0`, `align`, `mode`            | Sketch context. |
| `Circle`            | `radius`                       | `align`, `mode`                          | Sketch context. |
| `RegularPolygon`    | `radius, side_count`           | `major_radius=True`, `rotation`          | |
| `SlotOverall`       | `width, height`                | `rotation`, `align`, `mode`              | |
| `Trapezoid`         | `width, height, left_side_angle` | `right_side_angle`, `rotation`, `align`| |
| `Polygon`           | `*pts` (>=3 (x,y) tuples)      | `align`, `mode`                          | Closed polygon. |
| `Face`              | `outer_wire`                   | `inner_wires=()`                         | Use `Face(Wire.make_polygon(pts))` for arbitrary tooth profiles. |
| `Wire.make_polygon` | `points`                       | `close=True`                             | Returns a `Wire`. |

Lines / paths (build123d, inside `BuildLine`)
| Object        | Required args             | Optional args      | Notes |
|---------------|---------------------------|--------------------|-------|
| `Line`        | `start_pt, end_pt`        |                    | |
| `Polyline`    | `*pts`                    | `close=False`      | LINE-context only; do NOT use inside `BuildSketch`. |
| `Spline`      | `*pts`                    | `tangents`, `periodic` | |
| `RadiusArc`   | `start_pt, end_pt, radius`|                    | |
| `ThreePointArc` | `pt1, pt2, pt3`         |                    | |
| `JernArc`     | `start, tangent, radius, arc_size` |           | |

Operations (build123d)
| Object / call    | Required args                       | Optional args                | Notes |
|------------------|-------------------------------------|------------------------------|-------|
| `extrude`        | `to_extrude` (face/sketch)          | `amount`, `dir`, `until`, `both`, `taper`, `mode` | |
| `revolve`        | `profiles`                          | `axis=Axis.Z`, `revolution_arc=360`, `mode`       | |
| `loft`           | `sections`                          | `ruled=False`, `mode`        | All sections must be closed and compatible. |
| `sweep`          | `sections, path`                    | `multisection`, `is_frenet`, `transition`, `binormal`, `mode` | |
| `fillet`         | `objects, radius`                   |                              | |
| `chamfer`        | `objects, length`                   | `length2`, `angle`, `reference` | |
| `mirror`         | `objects`                           | `about=Plane.XZ`, `mode`     | |
| `offset`         | `objects, amount`                   | `openings`, `kind="arc"`, `mode` | |
| `split`          | `objects`                           | `bisect_by=Plane.XZ`, `keep` | |
| `Hole`           | `radius`                            | `depth=None`, `mode`         | `BuildPart` only; use for through/blind holes. |
| `CounterBoreHole`| `radius, counter_bore_radius, counter_bore_depth` | `depth`         | |
| `CounterSinkHole`| `radius, counter_sink_radius`       | `counter_sink_angle=82`, `depth` | |

Placement / transforms (build123d)
| Object         | Required args              | Notes |
|----------------|----------------------------|-------|
| `Pos`          | `x, y, z`                  | Translation. Use as `Pos(x,y,z) * shape`. |
| `Rot`          | `x_deg, y_deg, z_deg`      | POSITIONAL only — `Rot(z=...)` is INVALID. Use `Rot(0, 0, angle)`. |
| `Plane`        | `origin` or named (`Plane.XY`, `Plane.XZ`, `Plane.YZ`, `Plane.front`, etc.) | |
| `Location`     | `position` and/or `orientation` | Lower-level than `Pos` / `Rot`. |
| `Axis`         | named (`Axis.X`, `Axis.Y`, `Axis.Z`) or `(origin, direction)` | |

Booleans (build123d)
| Form              | Notes |
|-------------------|-------|
| `a + b`           | Union (also `mode=Mode.ADD` inside builders). |
| `a - b`           | Difference (also `mode=Mode.SUBTRACT`). |
| `a & b`           | Intersection (also `mode=Mode.INTERSECT`). |

bd_warehouse extensions
| Object                              | Required args                                          | Optional args                                            | Notes |
|-------------------------------------|--------------------------------------------------------|----------------------------------------------------------|-------|
| `bd_warehouse.gear.SpurGear`        | `module, tooth_count, pressure_angle, thickness`       | `root_fillet`, `addendum`, `dedendum`                    | Returns a `Part`. |
| `bd_warehouse.gear.SpurGearPlan`    | `module, tooth_count, pressure_angle`                  | `root_fillet`                                            | Returns a sketch/face. |
| `bd_warehouse.bearing.SingleRowDeepGrooveBallBearing` | `size` (e.g. `"M8-22-7"`)            |                                                          | |
| `bd_warehouse.bearing.PressFitHole` | `bearing`                                              | `fit="Normal"`, `depth`                                  | Used inside `BuildPart`. |
| `bd_warehouse.fastener.SocketHeadCapScrew` | `size` (e.g. `"M4-0.7"`), `length`              | `fastener_type="iso4762"`, `simple=True`                 | Use ClearanceHole/TapHole/ThreadedHole to mate. |
| `bd_warehouse.fastener.HexNut`      | `size`                                                 | `fastener_type="iso4032"`, `simple=True`                 | |
| `bd_warehouse.fastener.ClearanceHole` | `fastener`                                           | `depth`, `counter_sunk=False`, `fit="Normal"`            | `BuildPart` only. |
| `bd_warehouse.fastener.TapHole`     | `fastener`                                             | `depth`, `material`, `counter_sunk=False`                | |
| `bd_warehouse.fastener.ThreadedHole`| `fastener`                                             | `depth`, `simple=True`                                   | |
| `bd_warehouse.thread.IsoThread`     | `major_diameter, pitch, length`                        | `external=True`, `hand="right"` or `"left"`, `end_finishes` | |

py_gearworks extensions (angles in radians)
| Object                              | Required args                                          | Optional args                                            | Notes |
|-------------------------------------|--------------------------------------------------------|----------------------------------------------------------|-------|
| `HelicalGear`                       | `module, tooth_count, helix_angle, face_width, pressure_angle` | `profile_shift`, `addendum`, `dedendum`         | Helix angle in radians. |
| `BevelGear`                         | `module, tooth_count, pitch_angle, face_width`         | `pressure_angle`                                         | |
| `GearBuilder`                       | `gear`                                                 |                                                          | Use `.part` or `.part_transformed`. |

Common gotchas
- `Rot(z=...)` does NOT exist — use `Rot(0, 0, angle_deg)`.
- `Polyline` lives in line context (`BuildLine`) only. For closed polygons use `Face(Wire.make_polygon(pts))` or `Polygon(*pts)`.
- `extrude(amount=...)` requires a planar face/sketch; loft sections must be closed and compatible.
- `Hole` and friends only exist inside `BuildPart`; outside, subtract a `Cylinder` instead.
- All measurements are millimeters unless a library docstring says otherwise (py_gearworks angles are radians).
- `from build123d import *` is acceptable; keep extension imports explicit.
- Return one `Part` / `Solid` from `build_model(params, context)`.
"""


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


INSTRUCTIONS = f"""You are the CAD Designer specialist in a CAD design harness.

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
     are the best fit: {_available_libraries_text()}
     (e.g. fasteners, gear generation). These live in the formloop venv that
     ``cad build --python`` evaluates the model under, so they are importable.
   - Keep imports explicit and minimal; do not pull in uninstalled libraries.
   - Keep the source small and readable — the goal is a correct minimum solid.
   - Follow this syntax cheat sheet for available objects and required/optional
     arguments:

{BUILD123D_CHEAT_SHEET}

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


__all__ = [
    "AVAILABLE_BUILD123D_LIBRARIES",
    "BUILD123D_CHEAT_SHEET",
    "CadRevisionResult",
    "CadSourceResult",
    "build_cad_designer",
]
