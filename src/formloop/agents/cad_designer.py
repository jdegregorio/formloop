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


# ---------------------------------------------------------------------------
# Build123D Ecosystem Cheat Sheet
# ---------------------------------------------------------------------------
# This comprehensive reference is injected directly into the designer's
# instructions so the LLM can author correct build123d source without
# guessing at constructor signatures.  It covers:
#   1. Build123D core  (primitives, sketch objects, curves, operations, etc.)
#   2. bd_warehouse    (fasteners, bearings, threads, flanges, pipes, sprockets, gears)
#   3. py_gearworks    (involute/cycloid/bevel gear generation)
#
# Notation:
#   REQ  = required positional/keyword argument
#   OPT  = optional keyword argument (default shown)
# ---------------------------------------------------------------------------

BUILD123D_CHEAT_SHEET = r"""
=======================================================================
BUILD123D ECOSYSTEM CHEAT SHEET  (installed libraries only)
=======================================================================

All measurements are millimetres unless stated otherwise.
Import convention:  ``from build123d import *``

-----------------------------------------------------------------------
1. BUILD123D CORE
-----------------------------------------------------------------------

1.1  Builders (context managers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  BuildPart()           – 3-D solid context
  BuildSketch()         – 2-D face context
  BuildLine()           – 1-D edge/wire context

1.2  Location helpers (used inside builders)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  GridLocations(x_spacing, y_spacing, x_count, y_count)
  HexLocations(apothem, x_count, y_count)
  Locations(*pts)
  PolarLocations(radius, count, OPT start_angle=0, OPT angular_range=360,
                 OPT rotate=True)

1.3  3-D Part objects (BuildPart)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Box(length, width, height, OPT align=(Align.CENTER,...))
  Cylinder(radius, height, OPT arc_size=360, OPT align=...)
  Cone(bottom_radius, top_radius, height, OPT arc_size=360, OPT align=...)
  Sphere(radius, OPT arc_size1=-90, OPT arc_size2=90, OPT arc_size3=360,
         OPT align=...)
  Torus(major_radius, minor_radius, OPT major_arc_size=360,
        OPT minor_arc_size1=0, OPT minor_arc_size2=360, OPT align=...)
  Wedge(xsize, ysize, zsize, xmin, zmin, xmax, zmax, OPT align=...)
  ConvexPolyhedron(pts)
  Hole(radius, OPT depth=None, OPT mode=Mode.SUBTRACT)
  CounterBoreHole(radius, counter_bore_radius, counter_bore_depth,
                  OPT depth=None, OPT mode=Mode.SUBTRACT)
  CounterSinkHole(radius, counter_sink_radius,
                  OPT counter_sink_angle=82, OPT depth=None,
                  OPT mode=Mode.SUBTRACT)

1.4  2-D Sketch objects (BuildSketch)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Circle(radius, OPT align=...)
  Ellipse(x_radius, y_radius, OPT align=...)
  Rectangle(width, height, OPT align=...)
  RectangleRounded(width, height, radius, OPT align=...)
  Polygon(*pts, OPT align=...)
  RegularPolygon(radius, side_count, OPT major_radius=None, OPT align=...)
  Trapezoid(width, height, left_side_angle, OPT right_side_angle=None,
            OPT align=...)
  Triangle(a, b, c, OPT align=...)     – side lengths
  SlotOverall(width, height, OPT rotation=0, OPT align=...)
  SlotCenterToCenter(center_separation, height, OPT rotation=0, OPT align=...)
  SlotCenterPoint(center, point, height, OPT align=...)
  SlotArc(arc, height, OPT rotation=0, OPT align=...)
  Text(txt, font_size, OPT font="Arial", OPT font_style=FontStyle.REGULAR,
       OPT align=...)

1.5  1-D Curve objects (BuildLine)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Line(start, end)
  Polyline(*pts, OPT close=False)
  PolarLine(start, length, OPT angle=None, OPT direction=None)
  CenterArc(center, radius, start_angle, arc_size)
  RadiusArc(start, end, radius)
  SagittaArc(start, end, sagitta)
  TangentArc(*pts, OPT tangent=None)
  ThreePointArc(p1, p2, p3)
  Spline(*pts, OPT tangents=None, OPT periodic=False)
  Bezier(*pts)
  Helix(pitch, height, radius, OPT center=(0,0,0),
        OPT direction=(0,0,1), OPT cone_angle=0, OPT lefthanded=False)
  FilletPolyline(*pts, radius)
  EllipticalCenterArc(center, x_radius, y_radius, start_angle, end_angle,
                      OPT rotation=0)

1.6  Operations
~~~~~~~~~~~~~~~~
  --- generic (all builders) ---
  add(obj)
  mirror(about=Plane.XZ)
  offset(amount, OPT kind=Kind.ARC)
  scale(factor)
  split(bisect_by=Plane.XZ, OPT keep=Keep.TOP)
  bounding_box(OPT mode=Mode.PRIVATE)
  project(obj, OPT workplane=Plane.XY)

  --- sketch / part ---
  chamfer(objects, length, OPT length2=None, OPT angle=None)
  fillet(objects, radius)

  --- sketch only ---
  full_round(edge)
  make_face()
  make_hull()
  sweep(path, OPT multisection=False)
  trace(line, OPT line_width=1)

  --- part only ---
  extrude(amount=None, OPT dir=None, OPT until=None, OPT both=False,
          OPT taper=0)
  revolve(axis=Axis.Z, OPT revolution_arc=360)
  loft(OPT ruled=False)
  sweep(path, OPT multisection=False, OPT transition=Transition.RIGHT)
  section(OPT by_plane=Plane.XY)
  draft(faces, plane, angle)

1.7  Boolean operators (algebra mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  solid_a + solid_b     – union
  solid_a - solid_b     – difference
  solid_a & solid_b     – intersection

1.8  Positioning helpers (algebra mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Pos(x=0, y=0, z=0)               – translate
  Rot(x=0, y=0, z=0)               – rotate (degrees, intrinsic Euler)
  Pos(x,y,z) * Rot(rx,ry,rz)       – combined
  obj.moved(Location((...), (...))) – explicit

1.9  Topology selectors
~~~~~~~~~~~~~~~~~~~~~~~~
  .vertices(), .edges(), .wires(), .faces(), .solids()
  .edges() > Axis.Z          – sort ascending
  .edges() < Axis.Z          – sort descending
  .faces() >> Axis.Z          – group_by, take last
  .faces() << Axis.Z          – group_by, take first
  .faces() | Plane.XY         – filter_by(GeomType/Axis/Plane)
  .filter_by_position(axis, min, max)

1.10  Useful enums
~~~~~~~~~~~~~~~~~~
  Align:       MIN, CENTER, MAX
  Mode:        ADD, SUBTRACT, INTERSECT, REPLACE, PRIVATE
  Keep:        TOP, BOTTOM, BOTH, ALL, INSIDE, OUTSIDE
  Kind:        ARC, INTERSECTION, TANGENT
  Until:       FIRST, LAST, NEXT, PREVIOUS
  Transition:  RIGHT, ROUND, TRANSFORMED
  FontStyle:   REGULAR, BOLD, ITALIC, BOLDITALIC
  SortBy:      LENGTH, RADIUS, AREA, VOLUME, DISTANCE
  GeomType:    LINE, CIRCLE, ELLIPSE, PLANE, CYLINDER, CONE, SPHERE, TORUS,
               BEZIER, BSPLINE, REVOLUTION, EXTRUSION, OFFSET, OTHER

1.11  Key direct-API classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Vector(x, y, z)
  Axis(origin, direction)       – e.g. Axis.X, Axis.Z
  Plane(origin, x_dir, z_dir)   – e.g. Plane.XY, Plane.XZ
  Location(pos_tuple, rot_tuple)
  Face, Edge, Wire, Shell, Solid, Compound
  Wire.make_polygon(pts, close=True) → Wire
  Face(Wire)  → planar face from closed wire
  export_step(shape, "path.step")
  import_step("path.step")

-----------------------------------------------------------------------
2. BD_WAREHOUSE  (from bd_warehouse.*)
-----------------------------------------------------------------------
Import examples:
  from bd_warehouse.fastener import SocketHeadCapScrew, HexNut, ClearanceHole
  from bd_warehouse.bearing import SingleRowDeepGrooveBallBearing, PressFitHole
  from bd_warehouse.thread import IsoThread
  from bd_warehouse.flange import SlipOnFlange, WeldNeckFlange
  from bd_warehouse.pipe import Pipe
  from bd_warehouse.sprocket import Sprocket
  from bd_warehouse.gear import SpurGear as BdWarehouseSpurGear

2.1  Fasteners  (bd_warehouse.fastener)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Base classes — all share:
    .types() → set[str]         – available type ids
    .sizes(type_id) → list[str] – sizes for that type
    .select_by_size(size) → dict

  Nuts:
    HexNut(size, fastener_type, OPT hand="right", OPT simple=True)
      fastener_type: "iso4032" | "iso4033" | "iso4035"
    HexNutWithFlange(size, fastener_type, ...)     – "din1665"
    DomedCapNut(size, fastener_type, ...)           – "din1587"
    UnchamferedHexagonNut(size, fastener_type, ...) – "iso4036"
    SquareNut(size, fastener_type, ...)             – "din557"
    HeatSetNut(size, fastener_type, ...)            – "McMaster-Carr" | "Hilitchi"

  Screws:
    SocketHeadCapScrew(size, length, fastener_type,
                       OPT hand="right", OPT simple=True)
      fastener_type: "iso4762" | "asme_b18.3"
    ButtonHeadScrew(...)        – "iso7380_1"
    ButtonHeadWithCollarScrew   – "iso7380_2"
    CheeseHeadScrew(...)        – "iso14580" | "iso7048" | "iso1207"
    CounterSunkScrew(...)       – "iso2009" | "iso14582" | "iso14581" |
                                  "iso10642" | "iso7046"
    HexHeadScrew(...)           – "iso4017" | "din931" | "iso4014"
    HexHeadWithFlangeScrew(...) – "din1662" | "din1665"
    PanHeadScrew(...)           – "asme_b_18.6.3" | "iso1580" | "iso14583"
    PanHeadWithCollarScrew(...) – "din967"
    RaisedCheeseHeadScrew(...)  – "iso7045"
    RaisedCounterSunkOvalHeadScrew – "iso2010" | "iso7047" | "iso14584"
    SetScrew(...)               – "iso4026"

  Washers:
    PlainWasher(size, fastener_type)
      fastener_type: "iso7094" | "iso7093" | "iso7089" | "iso7091"
    ChamferedWasher(...)  – "iso7090"
    CheeseHeadWasher(...) – "iso7092"

  Custom holes (used inside BuildPart):
    ClearanceHole(fastener, OPT fit="Normal", OPT depth=None,
                  OPT wash=False, OPT wash_type=None,
                  OPT counter_sunk=None, OPT mode=Mode.SUBTRACT)
    TapHole(fastener, OPT material="Soft", OPT depth=None,
            OPT mode=Mode.SUBTRACT)
    InsertHole(fastener, OPT depth=None, OPT mode=Mode.SUBTRACT)
    ThreadedHole(fastener, OPT depth=None, OPT mode=Mode.SUBTRACT)

2.2  Bearings  (bd_warehouse.bearing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  SingleRowDeepGrooveBallBearing(size, OPT bearing_type="SKT")
    size format: "M8-22-7" (bore-OD-width)
  SingleRowCappedDeepGrooveBallBearing(size, OPT bearing_type="SKT")
  SingleRowAngularContactBallBearing(size, OPT bearing_type="SKT")
  SingleRowCylindricalRollerBearing(size, OPT bearing_type="SKT")
  PressFitHole(bearing, OPT interference=0, OPT fit="Normal",
               OPT depth=None, OPT mode=Mode.SUBTRACT)

2.3  Threads  (bd_warehouse.thread)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  IsoThread(major_diameter, pitch, length, OPT external=True,
            OPT hand="right", OPT end_finishes=("fade","fade"))
  AcmeThread(size, length, OPT external=True, OPT hand="right",
             OPT end_finishes=("fade","fade"))
  MetricTrapezoidalThread(size, length, OPT external=True, ...)
  TrapezoidalThread(size, length, OPT external=True, ...)
  PlasticBottleThread(size, OPT external=True, OPT hand="right")

2.4  Flanges  (bd_warehouse.flange)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  SlipOnFlange(nps, flange_class, face_type)
  WeldNeckFlange(nps, flange_class, face_type)
  BlindFlange(nps, flange_class, face_type)
  nps: float (nominal pipe size, inches)
  flange_class: 150 | 300 | 600 | 900 | 1500 | 2500
  face_type: "Flat" | "Raised"

2.5  Pipes  (bd_warehouse.pipe)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Pipe(nps, material, identifier, OPT path=None, OPT length=None)
    e.g. Pipe(nps=1, material="carbon", identifier="40")

2.6  Sprockets  (bd_warehouse.sprocket)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Sprocket(num_teeth, chain_pitch, roller_diameter,
           OPT clearance=0, OPT thickness=None)

2.7  Gears  (bd_warehouse.gear)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  SpurGear(module, num_teeth, face_width,
           OPT pressure_angle=20, OPT backlash=0)

-----------------------------------------------------------------------
3. PY_GEARWORKS  (from py_gearworks import *)
-----------------------------------------------------------------------
Accurate involute/cycloid/bevel gear geometry built on build123d.

  Gear types:
    SpurGear(number_of_teeth, module, height,
             OPT pressure_angle=20, OPT profile_shift=0,
             OPT helix_angle=0, OPT backlash=0)
    HelicalGear(number_of_teeth, module, height,
                helix_angle, OPT pressure_angle=20,
                OPT profile_shift=0, OPT backlash=0)
    HerringboneGear(number_of_teeth, module, height,
                    helix_angle, OPT pressure_angle=20,
                    OPT profile_shift=0, OPT backlash=0)
    RingGear(number_of_teeth, module, height,
             OPT pressure_angle=20, OPT profile_shift=0,
             OPT helix_angle=0, OPT backlash=0)
    BevelGear(number_of_teeth, module, height,
              cone_angle, OPT pressure_angle=20,
              OPT profile_shift=0, OPT spiral_angle=0,
              OPT backlash=0)
    CycloidGear(number_of_teeth, module, height,
                OPT profile_shift=0, OPT backlash=0)

  Key methods:
    gear.build_part() → Part        – generate the build123d solid
    gear.mesh_to(other_gear, target_dir=UP,
                 OPT backlash=0, OPT angle_bias=0)
                                    – position gear relative to mate

  Useful properties:
    gear.center_location_top        – Location for placing features on top
    gear.center_location_bottom     – Location for placing features on bottom
    gear.transform                  – the gear's 4x4 transform

  Direction constants:
    UP, DOWN, LEFT, RIGHT, IN, OUT

  Note: py_gearworks gears generate their own tooth profiles analytically.
  After build_part(), use standard build123d booleans:
    gear_part = gear.build_part()
    gear_part = gear_part.cut(some_hole)

=======================================================================
"""

INSTRUCTIONS = (
    """You are the CAD Designer specialist in a CAD design harness.

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
   - Consult the cheat sheet below for the full set of available primitives,
     operations, and extension libraries. Every class and function listed there
     is importable in the build environment.
   - Prefer clear build123d primitives first (Box, Cylinder, Sphere, Cone, Pos,
     Rot, boolean union (+), difference (-), intersection (&)).
   - You may also use the installed extension libraries ``bd_warehouse`` and
     ``py_gearworks`` when they are the best fit (e.g. fasteners, bearings,
     threads, gears). See the cheat sheet for exact import paths and
     constructor signatures.
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
- ``source`` must be executable Python text, not Markdown and not a patch.

"""
    + BUILD123D_CHEAT_SHEET
)


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
