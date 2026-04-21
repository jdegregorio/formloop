# Objects

_Source: [https://build123d.readthedocs.io/en/latest/objects.html](https://build123d.readthedocs.io/en/latest/objects.html)_

_Part of the Build123D knowledge pack (formloop/src/formloop/agents/knowledge/build123d/pages/objects.md)._

---

# Objects

Objects are Python classes that take parameters as inputs and create 1D, 2D or 3D Shapes.
For example, a [`Torus`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Torus "objects_part.Torus") is defined by a major and minor radii. In
Builder mode, objects are positioned with `Locations` while in Algebra mode, objects
are positioned with the `*` operator and shown in these examples:

```python
```build123d
with BuildPart() as disk:
    with BuildSketch():
        Circle(a)
        with Locations((b, 0.0)):
            Rectangle(c, c, mode=Mode.SUBTRACT)
        with Locations((0, b)):
            Circle(d, mode=Mode.SUBTRACT)
    extrude(amount=c)
```

```python
```build123d
sketch = Circle(a) - Pos(b, 0.0) * Rectangle(c, c) - Pos(0.0, b) * Circle(d)
disk = extrude(sketch, c)
```

The following sections describe the 1D, 2D and 3D objects:

## Align

2D/Sketch and 3D/Part objects can be aligned relative to themselves, either centered, or justified
right or left of each Axis. The following diagram shows how this alignment works in 2D:

![_images/align.svg](https://build123d.readthedocs.io/en/latest/_images/align.svg)

For example:

```python
```build123d
with BuildSketch():
    Circle(1, align=(Align.MIN, Align.MIN))
```

creates a circle who’s minimal X and Y values are on the X and Y axis and is located in the top right corner.
The `Align` enum has values: `MIN`, `CENTER` and `MAX`.

In 3D the `align` parameter also contains a Z align value but otherwise works in the same way.

Note that the `align` will also accept a single `Align` value which will be used on all axes -
as shown here:

```python
```build123d
with BuildSketch():
    Circle(1, align=Align.MIN)
```

## Mode

With the Builder API the `mode` parameter controls how objects are combined with lines, sketches, or parts
under construction. The `Mode` enum has values:

- `ADD`: fuse this object to the object under construction
- `SUBTRACT`: cut this object from the object under construction
- `INTERSECT`: intersect this object with the object under construction
- `REPLACE`: replace the object under construction with this object
- `PRIVATE`: don’t interact with the object under construction at all

The Algebra API doesn’t use the `mode` parameter - users combine objects with operators.

## 1D Objects

The following objects all can be used in BuildLine contexts. Note that
1D objects are not affected by `Locations` in Builder mode.

[`Airfoil`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.Airfoil "objects_curve.Airfoil")

![_images/example_airfoil.svg](https://build123d.readthedocs.io/en/latest/_images/example_airfoil.svg)

Airfoil described by 4 digit NACA profile

[`Bezier`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.Bezier "objects_curve.Bezier")

![_images/bezier_curve_example.svg](https://build123d.readthedocs.io/en/latest/_images/bezier_curve_example.svg)

Curve defined by control points and weights

[`BlendCurve`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.BlendCurve "objects_curve.BlendCurve")

![_images/example_blend_curve.svg](https://build123d.readthedocs.io/en/latest/_images/example_blend_curve.svg)

Curve blending curvature of two curves

[`CenterArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.CenterArc "objects_curve.CenterArc")

![_images/center_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/center_arc_example.svg)

Arc defined by center, radius, & angles

[`ConstrainedArcs`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.ConstrainedArcs "objects_curve.ConstrainedArcs")

![_images/constrained_arcs_example.svg](https://build123d.readthedocs.io/en/latest/_images/constrained_arcs_example.svg)

Arc(s) constrained by other geometric objects

[`ConstrainedLines`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.ConstrainedLines "objects_curve.ConstrainedLines")

![_images/constrained_lines_example.svg](https://build123d.readthedocs.io/en/latest/_images/constrained_lines_example.svg)

Line(s) constrained by other geometric objects

[`DoubleTangentArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.DoubleTangentArc "objects_curve.DoubleTangentArc")

![_images/double_tangent_line_example.svg](https://build123d.readthedocs.io/en/latest/_images/double_tangent_line_example.svg)

Arc defined by point/tangent pair & other curve

[`EllipticalCenterArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.EllipticalCenterArc "objects_curve.EllipticalCenterArc")

![_images/elliptical_center_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/elliptical_center_arc_example.svg)

Elliptical arc defined by center, radii & angles

[`EllipticalStartArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.EllipticalStartArc "objects_curve.EllipticalStartArc")

![_images/elliptical_start_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/elliptical_start_arc_example.svg)

Elliptical arc defined by start, tangent, radii & angles

[`ParabolicCenterArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.ParabolicCenterArc "objects_curve.ParabolicCenterArc")

![_images/parabolic_center_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/parabolic_center_arc_example.svg)

Parabolic arc defined by vertex, focal length & angles

[`HyperbolicCenterArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.HyperbolicCenterArc "objects_curve.HyperbolicCenterArc")

![_images/hyperbolic_center_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/hyperbolic_center_arc_example.svg)

Hyperbolic arc defined by center, radii & angles

[`FilletPolyline`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.FilletPolyline "objects_curve.FilletPolyline")

![_images/filletpolyline_example.svg](https://build123d.readthedocs.io/en/latest/_images/filletpolyline_example.svg)

Polyline with filleted corners defined by pts and radius

[`Helix`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.Helix "objects_curve.Helix")

![_images/helix_example.svg](https://build123d.readthedocs.io/en/latest/_images/helix_example.svg)

Helix defined pitch, radius and height

[`IntersectingLine`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.IntersectingLine "objects_curve.IntersectingLine")

![_images/intersecting_line_example.svg](https://build123d.readthedocs.io/en/latest/_images/intersecting_line_example.svg)

Intersecting line defined by start, direction & other line

[`JernArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.JernArc "objects_curve.JernArc")

![_images/jern_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/jern_arc_example.svg)

Arc define by start point, tangent, radius and angle

[`Line`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.Line "objects_curve.Line")

![_images/line_example.svg](https://build123d.readthedocs.io/en/latest/_images/line_example.svg)

Line defined by end points

[`PolarLine`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.PolarLine "objects_curve.PolarLine")

![_images/polar_line_example.svg](https://build123d.readthedocs.io/en/latest/_images/polar_line_example.svg)

Line defined by start, angle and length

[`Polyline`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.Polyline "objects_curve.Polyline")

![_images/polyline_example.svg](https://build123d.readthedocs.io/en/latest/_images/polyline_example.svg)

Multiple line segments defined by points

[`RadiusArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.RadiusArc "objects_curve.RadiusArc")

![_images/radius_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/radius_arc_example.svg)

Arc defined by two points and a radius

[`SagittaArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.SagittaArc "objects_curve.SagittaArc")

![_images/sagitta_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/sagitta_arc_example.svg)

Arc defined by two points and a sagitta

[`Spline`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.Spline "objects_curve.Spline")

![_images/spline_example.svg](https://build123d.readthedocs.io/en/latest/_images/spline_example.svg)

Curve define by points

[`TangentArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.TangentArc "objects_curve.TangentArc")

![_images/tangent_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/tangent_arc_example.svg)

Arc defined by two points and a tangent

[`ThreePointArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.ThreePointArc "objects_curve.ThreePointArc")

![_images/three_point_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/three_point_arc_example.svg)

Arc defined by three points

[`ArcArcTangentLine`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.ArcArcTangentLine "objects_curve.ArcArcTangentLine")

![_images/example_arc_arc_tangent_line.svg](https://build123d.readthedocs.io/en/latest/_images/example_arc_arc_tangent_line.svg)

Line tangent defined by two arcs

[`ArcArcTangentArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.ArcArcTangentArc "objects_curve.ArcArcTangentArc")

![_images/example_arc_arc_tangent_arc.svg](https://build123d.readthedocs.io/en/latest/_images/example_arc_arc_tangent_arc.svg)

Arc tangent defined by two arcs

[`PointArcTangentLine`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.PointArcTangentLine "objects_curve.PointArcTangentLine")

![_images/example_point_arc_tangent_line.svg](https://build123d.readthedocs.io/en/latest/_images/example_point_arc_tangent_line.svg)

Line tangent defined by a point and arc

[`PointArcTangentArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.PointArcTangentArc "objects_curve.PointArcTangentArc")

![_images/example_point_arc_tangent_arc.svg](https://build123d.readthedocs.io/en/latest/_images/example_point_arc_tangent_arc.svg)

Arc tangent defined by a point, direction, and arc

### Reference

*class* BaseLineObject(*curve: ~build123d.topology.one\_d.Wire*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   BaseLineObject specialized for Wire.

    Parameters:
    :   - **curve** ([*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – wire to create
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* Airfoil(*airfoil\_code: str*, *n\_points: int = 50*, *finite\_te: bool = False*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Create an airfoil described by a 4-digit (or fractional) NACA airfoil
    (e.g. ‘2412’ or ‘2213.323’).

    The NACA four-digit wing sections define the airfoil\_code by:
    - First digit describing maximum camber as percentage of the chord.
    - Second digit describing the distance of maximum camber from the airfoil leading edge
    in tenths of the chord.
    - Last two digits describing maximum thickness of the airfoil as percent of the chord.

    Parameters:
    :   - **airfoil\_code** – str
          The NACA 4-digit (or fractional) airfoil code (e.g. ‘2213.323’).
        - **n\_points** – int
          Number of points per upper/lower surface.
        - **finite\_te** – bool
          If True, enforces a finite trailing edge (default False).
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    *property* camber\_line*: Edge*
    :   Camber line of the airfoil as an Edge.

    camber\_pos*: float*
    :   Chordwise position of max camber (0–1)

    code*: str*
    :   NACA code string (e.g. “2412”)

    finite\_te*: bool*
    :   If True, trailing edge is finite

    max\_camber*: float*
    :   Maximum camber as fraction of chord

    *static* parse\_naca4(*value: str | float*) → tuple[float, float, float]
    :   Parse NACA 4-digit (or fractional) airfoil code into parameters.

    thickness*: float*
    :   Maximum thickness as fraction of chord

*class* Bezier(*\*cntl\_pnts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], weights: list[float] | None = None, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Bezier Curve

    Create a non-rational bezier curve defined by a sequence of points and include optional
    weights to create a rational bezier curve. The number of weights must match the number
    of control points.

    Parameters:
    :   - **cntl\_pnts** (*sequence**[**VectorLike**]*) – points defining the curve
        - **weights** (*list**[**float**]**,* *optional*) – control point weights. Defaults to None
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* BlendCurve(*curve0: ~build123d.topology.one\_d.Edge, curve1: ~build123d.topology.one\_d.Edge, continuity: ~build123d.build\_enums.ContinuityLevel = ContinuityLevel.C2, end\_points: tuple[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]] | None = None, tangent\_scalars: tuple[float, float] | None = None, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: BlendCurve

    Create a smooth Bézier-based transition curve between two existing edges.

    The blend is constructed as a cubic (C1) or quintic (C2) Bézier curve
    whose control points are determined from the position, first derivative,
    and (for C2) second derivative of the input curves at the chosen endpoints.
    Optional scalar multipliers can be applied to the endpoint tangents to
    control the “tension” of the blend.

    Parameters:
    :   - **curve0** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")) – First curve to blend from.
        - **curve1** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")) – Second curve to blend to.
        - **continuity** (*ContinuityLevel**,* *optional*) – Desired geometric continuity at the join:
          - ContinuityLevel.C0: position match only (straight line)
          - ContinuityLevel.C1: match position and tangent direction (cubic Bézier)
          - ContinuityLevel.C2: match position, tangent, and curvature (quintic Bézier)
          Defaults to ContinuityLevel.C2.
        - **end\_points** (*tuple**[**VectorLike**,* *VectorLike**]* *|* *None**,* *optional*) – Pair of points specifying the connection points on curve0 and curve1.
          Each must coincide (within TOLERANCE) with the start or end of the
          respective curve. If None, the closest pair of endpoints is chosen.
          Defaults to None.
        - **tangent\_scalars** (*tuple**[**float**,* *float**]* *|* *None**,* *optional*) – Scalar multipliers applied to the first derivatives at the start
          of curve0 and the end of curve1 before computing control points.
          Useful for adjusting the pull/tension of the blend without altering
          the base curves. Defaults to (1.0, 1.0).
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – Boolean operation mode when used in a
          BuildLine context. Defaults to Mode.ADD.

    Raises:
    :   - **ValueError** – tangent\_scalars must be a pair of float values.
        - **ValueError** – If specified end\_points are not coincident with the start
          or end of their respective curves.

    Example

    ```python
    ```default
    >>> blend = BlendCurve(curve_a, curve_b, ContinuityLevel.C1, tangent_scalars=(1.2, 0.8))
    >>> show(blend)
    ```
    ```

*class* CenterArc(*center: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], radius: float, start\_angle: float, arc\_size: float | ~build123d.topology.shape\_core.Shape | ~build123d.geometry.Axis | ~build123d.geometry.Location | ~build123d.geometry.Plane | ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Center Arc

    Create a circular arc defined by a center point and radius.

    Parameters:
    :   - **center** (*VectorLike*) – center point of arc
        - **radius** (*float*) – arc radius
        - **start\_angle** (*float*) – arc starting angle from x-axis
        - **arc\_size** (*float* *|* [*Shape*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape "topology.Shape") *|* [*Axis*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Axis "geometry.Axis") *|* [*Location*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Location "geometry.Location") *|* [*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane") *|* *VectorLike*) –

          angular size
          of arc or an arc limit.

          When a limit object is provided instead of a numeric angular size, CenterArc
          constructs the valid arc(s) from the given start point, trims them at their
          first intersection with the limit, and returns the one requiring the shortest
          travel from the start. Therefore, one can only generate arcs < 180° using a limit.
          If neither valid arc intersects the limit, a ValueError is raised.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* ConstrainedArcs(*tangency\_one: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *tangency\_two: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *\**, *radius: float*, *sagitta: Sagitta = Sagitta.SHORT*, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda arcs: ...*, *mode: Mode = Mode.ADD*)

*class* ConstrainedArcs(*tangency\_one: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *tangency\_two: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *\**, *center\_on: Axis | Edge*, *sagitta: Sagitta = Sagitta.SHORT*, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda arcs: ...*, *mode: Mode = Mode.ADD*)

*class* ConstrainedArcs(*tangency\_one: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *tangency\_two: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *tangency\_three: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *\**, *sagitta: Sagitta = Sagitta.SHORT*, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda arcs: ...*, *mode: Mode = Mode.ADD*)

*class* ConstrainedArcs(*tangency\_one: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *\**, *center: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda arcs: ...*, *mode: Mode = Mode.ADD*)

*class* ConstrainedArcs(*tangency\_one: tuple[Axis | Edge, Tangency] | Axis | Edge | Vertex | Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *\**, *radius: float*, *center\_on: Edge*, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda arcs: ...*, *mode: Mode = Mode.ADD*)
:   Line Object: Arc(s) constrained by other geometric objects.

    The result is always a Curve containing one or more Edges. If you need
    to access Edge-specific properties or methods (such as `arc_center`),
    extract the edge or edges first:

    ```python
    ```default
    result = ConstrainedArcs(...)
    arc = result.edge()           # extract the Edge
    center = arc.arc_center       # now Edge methods are available
    ```
    ```

    Note that in Builder mode the `selector` parameter must be provided or
    all results will be combined into the BuildLine context. In Algebra mode
    the selector can be applied as a parameter or in the normal way to the
    ConstrainedArcs object. The content of the selector is the same in both cases.

    Examples

    An arc built from three edge constraints.

    Algebra:

    ```python
    ```default
    l4 = PolarLine((0, 0), 4, 60)
    l5 = PolarLine((0, 0), 4, 40)
    a3 = CenterArc((0, 0), 4, 0, 90)
    ex_a3 = (
        ConstrainedArcs(l4, l5, a3, sagitta=Sagitta.BOTH).edges().sort_by(Edge.length)[0]
    )
    ```
    ```

    Builder:

    ```python
    ```default
    with BuildLine() as arc_ex3:
        l4 = PolarLine((0, 0), 4, 60)
        l5 = PolarLine((0, 0), 4, 40)
        a3 = CenterArc((0, 0), 4, 0, 90)
        ex_a3 = ConstrainedArcs(
            l4,
            l5,
            a3,
            sagitta=Sagitta.BOTH,
            selector=lambda arcs: arcs.sort_by(Edge.length)[0],
        )
    ```
    ```

*class* ConstrainedLines(*tangency\_one: tuple[Edge, Tangency] | Axis | Edge*, *tangency\_two: tuple[Edge, Tangency] | Axis | Edge*, *\**, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda lines: ...*, *mode: Mode = Mode.ADD*)

*class* ConstrainedLines(*tangency\_one: tuple[Edge, Tangency] | Edge*, *tangency\_two: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *\**, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda lines: ...*, *mode: Mode = Mode.ADD*)

*class* ConstrainedLines(*tangency\_one: tuple[Edge, Tangency] | Edge*, *tangency\_two: Axis*, *\**, *angle: float | None = None*, *direction: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float] | None = None*, *selector: Callable[[ShapeList[Edge]], Edge | ShapeList[Edge]] = lambda lines: ...*, *mode: Mode = Mode.ADD*)
:   Line Object: Lines(s) constrained by other geometric objects.

    The result is always a Curve containing one or more Edges. If you need
    to access Edge-specific properties or methods (such as `length`),
    extract the edge or edges first:

    ```python
    ```default
    result = ConstrainedLines(...)
    lines = result.edges()      # extract the Edges
    length = lines[1].length    # now Edge methods are available
    ```
    ```

    Note that in Builder mode the `selector` parameter must be provided or
    all results will be combined into the BuildLine context. In Algebra mode
    the selector can be applied as a parameter or in the normal way to the
    ConstrainedArcs object. The content of the selector is the same in both cases.

*class* DoubleTangentArc(*pnt: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], tangent: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], other: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire, keep: ~build123d.build\_enums.Keep = <Keep.TOP>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Double Tangent Arc

    Create a circular arc defined by a point/tangent pair and another line find a tangent to.

    The arc specified with TOP or BOTTOM depends on the geometry and isn’t predictable.

    Contains a solver.

    Parameters:
    :   - **pnt** (*VectorLike*) – start point
        - **tangent** (*VectorLike*) – tangent at start point
        - **other** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – line object to tangent
        - **keep** ([*Keep*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Keep "build_enums.Keep")*,* *optional*) – specify which arc if more than one, TOP or BOTTOM.
          Defaults to Keep.TOP
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **RunTimeError** – no double tangent arcs found

*class* EllipticalCenterArc(*center: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], x\_radius: float, y\_radius: float, start\_angle: float = 0.0, end\_angle: float | None = None, \*, arc\_size: float | ~build123d.topology.shape\_core.Shape | ~build123d.geometry.Axis | ~build123d.geometry.Location | ~build123d.geometry.Plane | ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] = 90.0, rotation: float = 0.0, angular\_direction: ~build123d.build\_enums.AngularDirection | None = None, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Elliptical Center Arc

    Create an elliptical arc defined by a center point, x- and y- radii.

    Parameters:
    :   - **center** (*VectorLike*) – ellipse center
        - **x\_radius** (*float*) – x radius of the ellipse (along the x-axis of plane)
        - **y\_radius** (*float*) – y radius of the ellipse (along the y-axis of plane)
        - **start\_angle** (*float**,* *optional*) – arc start angle from x-axis.
          Defaults to 0.0
        - **end\_angle** (*float* *|* *None*) – arc end angle from x-axis.
          Defaults to None
        - **arc\_size** (*float* *|* [*Shape*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape "topology.Shape") *|* [*Axis*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Axis "geometry.Axis") *|* [*Location*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Location "geometry.Location") *|* [*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane") *|* *VectorLike*) –

          angular size
          of arc (negative to change direction) or an arc limit.

          When a limit object is provided instead of a numeric angular size,
          EllipticalCenterArc constructs the valid arc(s) from the given start
          point, trims them at their first intersection with the limit, and
          returns the one requiring the shortest travel from the start.
          Therefore, one can only generate arcs < 180° using a limit. If
          neither valid arc intersects the limit, a ValueError is raised.
        - **rotation** (*float**,* *optional*) – angle to rotate arc. Defaults to 0.0
        - **angular\_direction** (*AngularDirection* *|* *None*) – arc direction.
          Defaults to None.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* EllipticalStartArc(*start\_pnt: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], start\_tangent: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], x\_radius: float, y\_radius: float, arc\_size: float, \*, start\_angle: float | None = None, major\_axis\_dir: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | None = None, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: EllipticalStartArc

    Create a circular arc defined by a start point/tangent pair, radius and arc size.

    Parameters:
    :   - **start\_pnt** (*VectorLike*) – start point
        - **start\_tangent** (*VectorLike*) – tangent at start point
        - **x\_radius** (*float*) – x radius of the ellipse (along the x-axis of plane)
        - **y\_radius** (*float*) – y radius of the ellipse (along the y-axis of plane)
        - **arc\_size** (*float*) – angular size of arc (negative to change direction)
        - **start\_angle** (*float*) – angular position of the start point
        - **major\_axis\_dir** (*VectorLike*) – direction of ellipse x-axis
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Note

    One of start\_angle or major\_axis\_dir must be provided.

*class* ParabolicCenterArc(*vertex: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], focal\_length: float, start\_angle: float = 0.0, end\_angle: float = 90.0, rotation: float = 0.0, angular\_direction: ~build123d.build\_enums.AngularDirection = <AngularDirection.COUNTER\_CLOCKWISE>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Parabolic Center Arc

    Create a parabolic arc defined by a vertex point and focal length (distance from focus to vertex).

    Parameters:
    :   - **vertex** (*VectorLike*) – parabola vertex
        - **focal\_length** (*float*) – focal length the parabola (distance from the vertex to focus along the x-axis of plane)
        - **start\_angle** (*float**,* *optional*) – arc start angle.
          Defaults to 0.0
        - **end\_angle** (*float**,* *optional*) – arc end angle.
          Defaults to 90.0
        - **rotation** (*float**,* *optional*) – angle to rotate arc. Defaults to 0.0
        - **angular\_direction** (*AngularDirection**,* *optional*) – arc direction.
          Defaults to AngularDirection.COUNTER\_CLOCKWISE
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* HyperbolicCenterArc(*center: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], x\_radius: float, y\_radius: float, start\_angle: float = 0.0, end\_angle: float = 90.0, rotation: float = 0.0, angular\_direction: ~build123d.build\_enums.AngularDirection = <AngularDirection.COUNTER\_CLOCKWISE>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Hyperbolic Center Arc

    Create a hyperbolic arc defined by a center point and focal length (distance from focus to vertex).

    Parameters:
    :   - **center** (*VectorLike*) – hyperbola center
        - **x\_radius** (*float*) – x radius of the ellipse (along the x-axis of plane)
        - **y\_radius** (*float*) – y radius of the ellipse (along the y-axis of plane)
        - **start\_angle** (*float**,* *optional*) – arc start angle from x-axis.
          Defaults to 0.0
        - **end\_angle** (*float**,* *optional*) – arc end angle from x-axis.
          Defaults to 90.0
        - **rotation** (*float**,* *optional*) – angle to rotate arc. Defaults to 0.0
        - **angular\_direction** (*AngularDirection**,* *optional*) – arc direction.
          Defaults to AngularDirection.COUNTER\_CLOCKWISE
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* FilletPolyline(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], radius: float | ~collections.abc.Iterable[float], close: bool = False, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Fillet Polyline
    Create a sequence of straight lines defined by successive points that are filleted
    to a given radius.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of two or more points
        - **radius** (*float* *|* *Iterable**[**float**]*) – radius to fillet at each vertex or a single value for all vertices.
          A radius of 0 will create a sharp corner (vertex without fillet).
        - **close** (*bool**,* *optional*) – close end points with extra Edge and corner fillets.
          Defaults to False
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   - **ValueError** – Two or more points not provided
        - **ValueError** – radius must be non-negative

*class* Helix(*pitch: float*, *height: float*, *radius: float*, *center: ~build123d.geometry.Vector | tuple[float*, *float] | tuple[float*, *float*, *float] | ~collections.abc.Sequence[float] = (0*, *0*, *0)*, *direction: ~build123d.geometry.Vector | tuple[float*, *float] | tuple[float*, *float*, *float] | ~collections.abc.Sequence[float] = (0*, *0*, *1)*, *cone\_angle: float = 0*, *lefthand: bool = False*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Helix

    Create a helix defined by pitch, height, and radius. The helix may have a taper
    defined by cone\_angle.

    If cone\_angle is not 0, radius is the initial helix radius at center. cone\_angle > 0
    increases the final radius. cone\_angle < 0 decreases the final radius.

    Parameters:
    :   - **pitch** (*float*) – distance between loops
        - **height** (*float*) – helix height
        - **radius** (*float*) – helix radius
        - **center** (*VectorLike**,* *optional*) – center point. Defaults to (0, 0, 0)
        - **direction** (*VectorLike**,* *optional*) – direction of central axis. Defaults to (0, 0, 1)
        - **cone\_angle** (*float**,* *optional*) – conical angle from direction.
          Defaults to 0
        - **lefthand** (*bool**,* *optional*) – left handed helix. Defaults to False
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* IntersectingLine(*start: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], direction: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], other: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Intersecting Line Object: Line

    Create a straight line defined by a point/direction pair and another line to intersect.

    Parameters:
    :   - **start** (*VectorLike*) – start point
        - **direction** (*VectorLike*) – direction to make line
        - **other** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")) – line object to intersect
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* JernArc(*start: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], tangent: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], radius: float, arc\_size: float | ~build123d.topology.shape\_core.Shape | ~build123d.geometry.Axis | ~build123d.geometry.Location | ~build123d.geometry.Plane | ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Jern Arc

    Create a circular arc defined by a start point/tangent pair, radius and arc size or arc limit.

    Parameters:
    :   - **start** (*VectorLike*) – start point
        - **tangent** (*VectorLike*) – tangent at start point
        - **radius** (*float*) – arc radius
        - **arc\_size** (*float* *|* [*Shape*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape "topology.Shape") *|* [*Axis*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Axis "geometry.Axis") *|* [*Location*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Location "geometry.Location") *|* [*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane") *|* *VectorLike*) –

          angular size
          of arc (negative to change direction) or an arc limit.

          When a limit object is provided instead of a numeric angular size, JernArc
          constructs the valid tangent arc(s) from the given start point and tangent,
          trims them at their first intersection with the limit, and returns the one
          requiring the shortest travel from the start. If neither valid arc intersects
          the limit, a ValueError is raised.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Variables:
    :   - **start** ([*Vector*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Vector "geometry.Vector")) – start point
        - **end\_of\_arc** ([*Vector*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Vector "geometry.Vector")) – end point of arc
        - **center\_point** ([*Vector*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Vector "geometry.Vector")) – center of arc

*class* Line(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Line

    Create a straight line defined by two points.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of two points
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – Two point not provided

*class* PolarLine(*start: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], length: float | ~build123d.topology.shape\_core.Shape | ~build123d.geometry.Axis | ~build123d.geometry.Location | ~build123d.geometry.Plane | ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], angle: float | None = None, direction: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | None = None, length\_mode: ~build123d.build\_enums.LengthMode = <LengthMode.DIAGONAL>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Polar Line

    Create a straight line defined by a start point, length, and angle.
    The length can specify the DIAGONAL, HORIZONTAL, or VERTICAL component of the triangle
    defined by the angle.

    Alternatively, the length parameter can contain a limit to the length of the line
    in the form of another object. If the PolarLine doesn’t contact the limit an error
    will be generated.

    Example

    p = PolarLine(start=(2, 0), length=Axis.Y, angle=135)

    Parameters:
    :   - **start** (*VectorLike*) – start point
        - **length** (*float* *|* [*Shape*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape "topology.Shape") *|* [*Axis*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Axis "geometry.Axis") *|* [*Location*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Location "geometry.Location") *|* [*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane") *|* *VectorLike*) – line length (float) or
          limit limit
        - **angle** (*float**,* *optional*) – angle from the local x-axis
        - **direction** (*VectorLike**,* *optional*) – vector direction to determine angle
        - **length\_mode** (*LengthMode**,* *optional*) – how length defines the line.
          Defaults to LengthMode.DIAGONAL
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   - **ValueError** – Either angle or direction must be provided
        - **ValueError** – Polar line doesn’t intersect length limit

*class* Polyline(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], close: bool = False, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Polyline

    Create a sequence of straight lines defined by successive points.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of two or more points
        - **close** (*bool**,* *optional*) – close by generating an extra Edge. Defaults to False
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – Two or more points not provided

*class* RadiusArc(*start\_point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], end\_point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], radius: float, short\_sagitta: bool = True, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Radius Arc

    Create a circular arc defined by two points and a radius.

    Parameters:
    :   - **start\_point** (*VectorLike*) – start point
        - **end\_point** (*VectorLike*) – end point
        - **radius** (*float*) – arc radius
        - **short\_sagitta** (*bool*) – If True selects the short sagitta (height of arc from
          chord), else the long sagitta crossing the center. Defaults to True
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – Insufficient radius to connect end points

*class* SagittaArc(*start\_point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], end\_point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], sagitta: float, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Sagitta Arc

    Create a circular arc defined by two points and the sagitta (height of the arc from chord).

    Parameters:
    :   - **start\_point** (*VectorLike*) – start point
        - **end\_point** (*VectorLike*) – end point
        - **sagitta** (*float*) – arc height from chord between points
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* Spline(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], tangents: ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]] | None = None, tangent\_scalars: ~collections.abc.Iterable[float] | None = None, periodic: bool = False, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Spline

    Create a spline defined by a sequence of points, optionally constrained by tangents.
    Tangents and tangent scalars must have length of 2 for only the end points or a length
    of the number of points.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of two or more points
        - **tangents** (*Iterable**[**VectorLike**]**,* *optional*) – tangent directions. Defaults to None
        - **tangent\_scalars** (*Iterable**[**float**]**,* *optional*) – tangent scales. Defaults to None
        - **periodic** (*bool**,* *optional*) – make the spline periodic (closed). Defaults to False
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* TangentArc(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], tangent: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], tangent\_from\_first: bool = True, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Tangent Arc

    Create a circular arc defined by two points and a tangent.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of two points
        - **tangent** (*VectorLike*) – tangent to constrain arc
        - **tangent\_from\_first** (*bool**,* *optional*) – apply tangent to first point. Applying
          tangent to end point will flip the orientation of the arc. Defaults to True
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – Two points are required

*class* ThreePointArc(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Three Point Arc

    Create a circular arc defined by three points.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of three points
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – Three points must be provided

*class* ArcArcTangentLine(*start\_arc: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire*, *end\_arc: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire*, *side: ~build123d.build\_enums.Side = <Side.LEFT>*, *keep: ~build123d.build\_enums.Keep = <Keep.INSIDE>*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Arc Arc Tangent Line

    Create a straight line tangent to two arcs.

    Parameters:
    :   - **start\_arc** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – starting arc, must be GeomType.CIRCLE
        - **end\_arc** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – ending arc, must be GeomType.CIRCLE
        - **side** (*Side*) – side of arcs to place tangent arc center, LEFT or RIGHT.
          Defaults to Side.LEFT
        - **keep** ([*Keep*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Keep "build_enums.Keep")) – which tangent arc to keep, INSIDE or OUTSIDE.
          Defaults to Keep.INSIDE
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* ArcArcTangentArc(*start\_arc: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire*, *end\_arc: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire*, *radius: float*, *side: ~build123d.build\_enums.Side = <Side.LEFT>*, *keep: ~build123d.build\_enums.Keep | tuple[~build123d.build\_enums.Keep*, *~build123d.build\_enums.Keep] = (<Keep.INSIDE>*, *<Keep.INSIDE>)*, *short\_sagitta: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Arc Arc Tangent Arc

    Create an arc tangent to two arcs and a radius.

    keep specifies tangent arc position with a Keep pair: (placement, type)

    - placement: start\_arc is tangent INSIDE or OUTSIDE the tangent arc. BOTH is a
      special case for overlapping arcs with type INSIDE
    - type: tangent arc is INSIDE or OUTSIDE start\_arc and end\_arc

    Parameters:
    :   - **start\_arc** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – starting arc, must be GeomType.CIRCLE
        - **end\_arc** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – ending arc, must be GeomType.CIRCLE
        - **radius** (*float*) – radius of tangent arc
        - **side** (*Side*) – side of arcs to place tangent arc center, LEFT or RIGHT.
          Defaults to Side.LEFT
        - **keep** ([*Keep*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Keep "build_enums.Keep") *|* *tuple**[*[*Keep*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Keep "build_enums.Keep")*,* [*Keep*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Keep "build_enums.Keep")*]*) – which tangent arc to keep, INSIDE or OUTSIDE.
          Defaults to (Keep.INSIDE, Keep.INSIDE)
        - **short\_sagitta** (*bool*) – If True selects the short sagitta (height of arc from
          chord), else the long sagitta crossing the center. Defaults to True
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

![ArcArcTangentArc keep table](https://build123d.readthedocs.io/en/latest/_images/arcarctangentarc_keep_table.png)

*class* PointArcTangentLine(*point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], arc: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire, side: ~build123d.build\_enums.Side = <Side.LEFT>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Point Arc Tangent Line

    Create a straight, tangent line from a point to a circular arc.

    Parameters:
    :   - **point** (*VectorLike*) – intersection point for tangent
        - **arc** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – circular arc to tangent, must be GeomType.CIRCLE
        - **side** (*Side**,* *optional*) – side of arcs to place tangent arc center, LEFT or RIGHT.
          Defaults to Side.LEFT
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* PointArcTangentArc(*point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], direction: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], arc: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire, side: ~build123d.build\_enums.Side = <Side.LEFT>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Line Object: Point Arc Tangent Arc

    Create an arc defined by a point/tangent pair and another line which the other end
    is tangent to.

    Parameters:
    :   - **point** (*VectorLike*) – starting point of tangent arc
        - **direction** (*VectorLike*) – direction at starting point of tangent arc
        - **arc** (*Union**[*[*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve")*,* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")*,* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")*]*) – ending arc, must be GeomType.CIRCLE
        - **side** (*Side**,* *optional*) – select which arc to keep Defaults to Side.LEFT
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   - **ValueError** – Arc must have GeomType.CIRCLE
        - **ValueError** – Point is already tangent to arc
        - **RuntimeError** – No tangent arc found

## 2D Objects

[`Arrow`](https://build123d.readthedocs.io/en/latest/objects.html#drafting.Arrow "drafting.Arrow")

![_images/arrow.svg](https://build123d.readthedocs.io/en/latest/_images/arrow.svg)

Arrow with head and path for shaft

[`ArrowHead`](https://build123d.readthedocs.io/en/latest/objects.html#drafting.ArrowHead "drafting.ArrowHead")

![_images/arrow_head.svg](https://build123d.readthedocs.io/en/latest/_images/arrow_head.svg)

Arrow head with multiple types

[`Circle`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Circle "objects_sketch.Circle")

![_images/circle_example.svg](https://build123d.readthedocs.io/en/latest/_images/circle_example.svg)

Circle defined by radius

[`DimensionLine`](https://build123d.readthedocs.io/en/latest/objects.html#drafting.DimensionLine "drafting.DimensionLine")

![_images/d_line.svg](https://build123d.readthedocs.io/en/latest/_images/d_line.svg)

Dimension line

[`Ellipse`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Ellipse "objects_sketch.Ellipse")

![_images/ellipse_example.svg](https://build123d.readthedocs.io/en/latest/_images/ellipse_example.svg)

Ellipse defined by major and minor radius

[`ExtensionLine`](https://build123d.readthedocs.io/en/latest/objects.html#drafting.ExtensionLine "drafting.ExtensionLine")

![_images/e_line.svg](https://build123d.readthedocs.io/en/latest/_images/e_line.svg)

Extension lines for distance or angles

[`Polygon`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Polygon "objects_sketch.Polygon")

![_images/polygon_example.svg](https://build123d.readthedocs.io/en/latest/_images/polygon_example.svg)

Polygon defined by points

[`Rectangle`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Rectangle "objects_sketch.Rectangle")

![_images/rectangle_example.svg](https://build123d.readthedocs.io/en/latest/_images/rectangle_example.svg)

Rectangle defined by width and height

[`RectangleRounded`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.RectangleRounded "objects_sketch.RectangleRounded")

![_images/rectangle_rounded_example.svg](https://build123d.readthedocs.io/en/latest/_images/rectangle_rounded_example.svg)

Rectangle with rounded corners defined by width, height, and radius

[`RegularPolygon`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.RegularPolygon "objects_sketch.RegularPolygon")

![_images/regular_polygon_example.svg](https://build123d.readthedocs.io/en/latest/_images/regular_polygon_example.svg)

RegularPolygon defined by radius and number of sides

[`SlotArc`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.SlotArc "objects_sketch.SlotArc")

![_images/slot_arc_example.svg](https://build123d.readthedocs.io/en/latest/_images/slot_arc_example.svg)

SlotArc defined by arc and height

[`SlotCenterPoint`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.SlotCenterPoint "objects_sketch.SlotCenterPoint")

![_images/slot_center_point_example.svg](https://build123d.readthedocs.io/en/latest/_images/slot_center_point_example.svg)

SlotCenterPoint defined by two points and a height

[`SlotCenterToCenter`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.SlotCenterToCenter "objects_sketch.SlotCenterToCenter")

![_images/slot_center_to_center_example.svg](https://build123d.readthedocs.io/en/latest/_images/slot_center_to_center_example.svg)

SlotCenterToCenter defined by center separation and height

[`SlotOverall`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.SlotOverall "objects_sketch.SlotOverall")

![_images/slot_overall_example.svg](https://build123d.readthedocs.io/en/latest/_images/slot_overall_example.svg)

SlotOverall defined by end-to-end length and height

[`TechnicalDrawing`](https://build123d.readthedocs.io/en/latest/objects.html#drafting.TechnicalDrawing "drafting.TechnicalDrawing")

![_images/tech_drawing.svg](https://build123d.readthedocs.io/en/latest/_images/tech_drawing.svg)

A technical drawing with descriptions

[`Text`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Text "objects_sketch.Text")

![_images/text_example.svg](https://build123d.readthedocs.io/en/latest/_images/text_example.svg)

Text defined by string and font parameters

[`Trapezoid`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Trapezoid "objects_sketch.Trapezoid")

![_images/trapezoid_example.svg](https://build123d.readthedocs.io/en/latest/_images/trapezoid_example.svg)

Trapezoid defined by width, height and interior angles

[`Triangle`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Triangle "objects_sketch.Triangle")

![_images/triangle_example.svg](https://build123d.readthedocs.io/en/latest/_images/triangle_example.svg)

Triangle defined by one side & two other sides or interior angles

### Reference

*class* BaseSketchObject(*obj: ~build123d.topology.composite.Compound | ~build123d.topology.two\_d.Face*, *rotation: float = 0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Base class for all BuildSketch objects

    Parameters:
    :   - **face** ([*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")) – face to create
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to None
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* Arrow(*arrow\_size: float*, *shaft\_path: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire*, *shaft\_width: float*, *head\_at\_start: bool = True*, *head\_type: ~build123d.build\_enums.HeadType = <HeadType.CURVED>*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Arrow with shaft

    Parameters:
    :   - **arrow\_size** (*float*) – arrow head tip to tail length
        - **shaft\_path** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – line describing the shaft shape
        - **shaft\_width** (*float*) – line width of shaft
        - **head\_at\_start** (*bool**,* *optional*) – Defaults to True.
        - **head\_type** (*HeadType**,* *optional*) – arrow head shape. Defaults to HeadType.CURVED.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – \_description\_. Defaults to Mode.ADD.

*class* ArrowHead(*size: float*, *head\_type: ~build123d.build\_enums.HeadType = <HeadType.CURVED>*, *rotation: float = 0*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: ArrowHead

    Parameters:
    :   - **size** (*float*) – tip to tail length
        - **head\_type** (*HeadType**,* *optional*) – arrow head shape. Defaults to HeadType.CURVED.
        - **rotation** (*float**,* *optional*) – rotation in degrees. Defaults to 0.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

*class* Circle(*radius: float*, *arc\_size: float = 360.0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Circle

    Create a circle defined by radius.

    Parameters:
    :   - **radius** (*float*) – circle radius
        - **arc\_size** (*float**,* *optional*) – angular size of sector. Defaults to 360.
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* DimensionLine(*path: ~build123d.topology.one\_d.Wire | ~build123d.topology.one\_d.Edge | list[~build123d.geometry.Vector | ~build123d.topology.zero\_d.Vertex | tuple[float, float, float]], draft: ~drafting.Draft, sketch: ~build123d.topology.composite.Sketch | None = None, label: str | None = None, arrows: tuple[bool, bool] = (True, True), tolerance: float | tuple[float, float] | None = None, label\_angle: bool = False, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: DimensionLine

    Create a dimension line typically for internal measurements.
    Typically used for (but not restricted to) inside dimensions, a dimension line often
    as arrows on either side of a dimension or label.

    There are three options depending on the size of the text and length
    of the dimension line:
    Type 1) The label and arrows fit within the length of the path
    Type 2) The text fit within the path and the arrows go outside
    Type 3) Neither the text nor the arrows fit within the path

    Parameters:
    :   - **path** (*PathDescriptor*) – a very general type of input used to describe the path the
          dimension line will follow.
        - **draft** (*Draft*) – instance of Draft dataclass
        - **sketch** ([*Sketch*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Sketch "topology.Sketch")) – the Sketch being created to check for possible overlaps. In builder
          mode the active Sketch will be used if None is provided.
        - **label** (*str**,* *optional*) – a text string which will replace the length (or
          arc length) that would otherwise be extracted from the provided path. Providing
          a label is useful when illustrating a parameterized input where the name of an
          argument is desired not an actual measurement. Defaults to None.
        - **arrows** (*tuple**[**bool**,* *bool**]**,* *optional*) – a pair of boolean values controlling the placement
          of the start and end arrows. Defaults to (True, True).
        - **tolerance** (*float* *|* *tuple**[**float**,* *float**]**,* *optional*) – an optional tolerance
          value to add to the extracted length value. If a single tolerance value is provided
          it is shown as ± the provided value while a pair of values are shown as
          separate + and - values. Defaults to None.
        - **label\_angle** (*bool**,* *optional*) – a flag indicating that instead of an extracted length value,
          the size of the circular arc extracted from the path should be displayed in degrees.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   - **ValueError** – Only 2 points allowed for dimension lines
        - **ValueError** – No output - no arrows selected

    dimension
    :   length of the dimension

*class* Ellipse(*x\_radius: float*, *y\_radius: float*, *rotation: float = 0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Ellipse

    Create an ellipse defined by x- and y- radii.

    Parameters:
    :   - **x\_radius** (*float*) – x radius of the ellipse (along the x-axis of plane)
        - **y\_radius** (*float*) – y radius of the ellipse (along the y-axis of plane)
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* ExtensionLine(*border: ~build123d.topology.one\_d.Wire | ~build123d.topology.one\_d.Edge | list[~build123d.geometry.Vector | ~build123d.topology.zero\_d.Vertex | tuple[float, float, float]], offset: float, draft: ~drafting.Draft, sketch: ~build123d.topology.composite.Sketch | None = None, label: str | None = None, arrows: tuple[bool, bool] = (True, True), tolerance: float | tuple[float, float] | None = None, label\_angle: bool = False, measurement\_direction: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | None = None, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Extension Line

    Create a dimension line with two lines extending outward from the part to dimension.
    Typically used for (but not restricted to) outside dimensions, with a pair of lines
    extending from the edge of a part to a dimension line.

    Parameters:
    :   - **border** (*PathDescriptor*) – a very general type of input defining the object to
          be dimensioned. Typically this value would be extracted from the part but is
          not restricted to this use.
        - **offset** (*float*) – a distance to displace the dimension line from the edge of the object
        - **draft** (*Draft*) – instance of Draft dataclass
        - **label** (*str**,* *optional*) – a text string which will replace the length (or arc length)
          that would otherwise be extracted from the provided path. Providing a label is
          useful when illustrating a parameterized input where the name of an argument
          is desired not an actual measurement. Defaults to None.
        - **arrows** (*tuple**[**bool**,* *bool**]**,* *optional*) – a pair of boolean values controlling the placement
          of the start and end arrows. Defaults to (True, True).
        - **tolerance** (*float* *|* *tuple**[**float**,* *float**]**,* *optional*) – an optional tolerance
          value to add to the extracted length value. If a single tolerance value is provided
          it is shown as ± the provided value while a pair of values are shown as
          separate + and - values. Defaults to None.
        - **label\_angle** (*bool**,* *optional*) – a flag indicating that instead of an extracted length
          value, the size of the circular arc extracted from the path should be displayed
          in degrees. Defaults to False.
        - **measurement\_direction** (*VectorLike**,* *optional*) – Vector line which to project the dimension
          against. Offset start point is the position of the start of border.
          Defaults to None.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    dimension
    :   length of the dimension

*class* Polygon(*\*pts: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float] | ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], rotation: float = 0, align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align, ~build123d.build\_enums.Align] | None = (<Align.NONE>, <Align.NONE>), mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Polygon

    Create a polygon defined by given sequence of points.

    Note: the order of the points defines the resulting normal of the Face in Algebra
    mode, where counter-clockwise order creates an upward normal while clockwise order
    a downward normal. In Builder mode, the Face is added with an upward normal.

    Parameters:
    :   - **pts** (*VectorLike* *|* *Iterable**[**VectorLike**]*) – sequence of points defining the
          vertices of the polygon
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.NONE, Align.NONE)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* Rectangle(*width: float*, *height: float*, *rotation: float = 0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Rectangle

    Create a rectangle defined by width and height.

    Parameters:
    :   - **width** (*float*) – rectangle width
        - **height** (*float*) – rectangle height
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* RectangleRounded(*width: float*, *height: float*, *radius: float*, *rotation: float = 0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Rectangle Rounded

    Create a rectangle defined by width and height with filleted corners.

    Parameters:
    :   - **width** (*float*) – rectangle width
        - **height** (*float*) – rectangle height
        - **radius** (*float*) – fillet radius
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* RegularPolygon(*radius: float*, *side\_count: int*, *major\_radius: bool = True*, *rotation: float = 0*, *align: tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Regular Polygon

    Create a regular polygon defined by radius and side count. Use major\_radius to define whether
    the polygon circumscribes (along the vertices) or inscribes (along the sides) the radius circle.

    Parameters:
    :   - **radius** (*float*) – construction radius
        - **side\_count** (*int*) – number of sides
        - **major\_radius** (*bool*) – If True the radius is the major radius (circumscribed circle),
          else the radius is the minor radius (inscribed circle). Defaults to True
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    apothem*: float*
    :   radius of the inscribed circle or minor radius

    radius*: float*
    :   radius of the circumscribed circle or major radius

*class* SlotArc(*arc: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire*, *height: float*, *rotation: float = 0*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Slot Arc

    Create a slot defined by a line and height. May be an arc, stright line, spline, etc.

    Parameters:
    :   - **arc** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")) – center line of slot
        - **height** (*float*) – diameter of end arcs
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* SlotCenterPoint(*center: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], point: ~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float], height: float, rotation: float = 0, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Slot Center Point

    Create a slot defined by the center of the slot and the center of one end arc.
    The slot will be symmetric about the center point.

    Parameters:
    :   - **center** (*VectorLike*) – center point
        - **point** (*VectorLike*) – center of arc point
        - **height** (*float*) – diameter of end arcs
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* SlotCenterToCenter(*center\_separation: float*, *height: float*, *rotation: float = 0*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Slot Center To Center

    Create a slot defined by the distance between the centers of the two end arcs.

    Parameters:
    :   - **center\_separation** (*float*) – distance between arc centers
        - **height** (*float*) – diameter of end arcs
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* SlotOverall(*width: float*, *height: float*, *rotation: float = 0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Slot Overall

    Create a slot defined by the overall width and height.

    Parameters:
    :   - **width** (*float*) – overall width of slot
        - **height** (*float*) – diameter of end arcs
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* TechnicalDrawing(*designed\_by: str = 'build123d'*, *design\_date: ~datetime.date | None = None*, *page\_size: ~build123d.build\_enums.PageSize = <PageSize.A4>*, *title: str = 'Title'*, *sub\_title: str = 'Sub Title'*, *drawing\_number: str = 'B3D-1'*, *sheet\_number: int | None = None*, *drawing\_scale: float = 1.0*, *nominal\_text\_size: float = 10.0*, *line\_width: float = 0.5*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: TechnicalDrawing

    The border of a technical drawing with external frame and text box.

    Parameters:
    :   - **designed\_by** (*str**,* *optional*) – Defaults to “build123d”.
        - **design\_date** (*date**,* *optional*) – Defaults to date.today().
        - **page\_size** (*PageSize**,* *optional*) – Defaults to PageSize.A4.
        - **title** (*str**,* *optional*) – drawing title. Defaults to “Title”.
        - **sub\_title** (*str**,* *optional*) – drawing sub title. Defaults to “Sub Title”.
        - **drawing\_number** (*str**,* *optional*) – Defaults to “B3D-1”.
        - **sheet\_number** (*int**,* *optional*) – Defaults to None.
        - **drawing\_scale** (*float**,* *optional*) – displays as 1:value. Defaults to 1.0.
        - **nominal\_text\_size** (*float**,* *optional*) – size of title text. Defaults to 10.0.
        - **line\_width** (*float**,* *optional*) – Defaults to 0.5.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    margin *= 5*

    page\_sizes *= {<PageSize.A0>: (1189, 841), <PageSize.A10>: (37, 26), <PageSize.A1>: (841, 594), <PageSize.A2>: (594, 420), <PageSize.A3>: (420, 297), <PageSize.A4>: (297, 210), <PageSize.A5>: (210, 148.5), <PageSize.A6>: (148.5, 105), <PageSize.A7>: (105, 74), <PageSize.A8>: (74, 52), <PageSize.A9>: (52, 37), <PageSize.LEDGER>: (431.79999999999995, 279.4), <PageSize.LEGAL>: (355.59999999999997, 215.89999999999998), <PageSize.LETTER>: (279.4, 215.89999999999998)}*

*class* Text(*txt: str*, *font\_size: float*, *font: str = 'Arial'*, *font\_path: ~os.PathLike[str] | str | None = None*, *font\_style: ~build123d.build\_enums.FontStyle = <FontStyle.REGULAR>*, *text\_align: tuple[~build123d.build\_enums.TextAlign*, *~build123d.build\_enums.TextAlign] = (<TextAlign.CENTER>*, *<TextAlign.CENTER>)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = None*, *path: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | None = None*, *position\_on\_path: float = 0.0*, *single\_line\_width: float | None = None*, *rotation: float = 0.0*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Text

    Create text defined by text string and font size.

    Fonts installed to the system can be specified by name and FontStyle. Fonts with
    subfamilies not in FontStyle should be specified with the subfamily name, e.g.
    “Arial Black”. Alternatively, a specific font file can be specified with font\_path.

    Use available\_fonts() to list available font names for font and FontStyles.
    Note: on Windows, fonts must be installed with “Install for all users” to be found
    by name.

    Not all fonts have every FontStyle available, however ITALIC and BOLDITALIC will
    still italicize the font if the respective font file is not available.

    text\_align specifies alignment of text inside the bounding box, while align the
    aligns the bounding box itself.

    Optionally, the Text can be positioned on a non-linear edge or wire with a path and
    position\_on\_path.

    Parameters:
    :   - **txt** (*str*) – text to render
        - **font\_size** (*float*) – size of the font in model units
        - **font** (*str**,* *optional*) – font name. Defaults to “Arial”
        - **font\_path** (*PathLike* *|* *str**,* *optional*) – system path to font file. Defaults to None
        - **font\_style** (*Font\_Style**,* *optional*) – font style, REGULAR, BOLD, BOLDITALIC, or
          ITALIC. Defaults to Font\_Style.REGULAR
        - **text\_align** (*tuple**[**TextAlign**,* *TextAlign**]**,* *optional*) – horizontal text align
          LEFT, CENTER, or RIGHT. Vertical text align BOTTOM, CENTER, TOP, or
          TOPFIRSTLINE. Defaults to (TextAlign.CENTER, TextAlign.CENTER)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of
          object. Defaults to None
        - **path** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")*,* *optional*) – path for text to follow. Defaults to None
        - **position\_on\_path** (*float**,* *optional*) – the relative location on path to position
          the text, values must be between 0.0 and 1.0. Defaults to 0.0
        - **single\_line\_width** (*float**,* *optional*) – width of outlined single line font.
          Defaults to 4% of font\_size
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* Trapezoid(*width: float*, *height: float*, *left\_side\_angle: float*, *right\_side\_angle: float | None = None*, *rotation: float = 0*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = (<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Trapezoid

    Create a trapezoid defined by major width, height, and interior angle(s).

    Parameters:
    :   - **width** (*float*) – trapezoid major width
        - **height** (*float*) – trapezoid height
        - **left\_side\_angle** (*float*) – bottom left interior angle
        - **right\_side\_angle** (*float**,* *optional*) – bottom right interior angle. If not provided,
          the trapezoid will be symmetric. Defaults to None
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to (Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – Give angles result in an invalid trapezoid

*class* Triangle(*\**, *a: float | None = None*, *b: float | None = None*, *c: float | None = None*, *A: float | None = None*, *B: float | None = None*, *C: float | None = None*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = None*, *rotation: float = 0*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Sketch Object: Triangle

    Create a triangle defined by one side length and any of two other side lengths or interior
    angles. The interior angles are opposite the side with the same designation
    (i.e. side ‘a’ is opposite angle ‘A’). Side ‘a’ is the bottom side, followed by ‘b’
    on the right, going counter-clockwise.

    Parameters:
    :   - **a** (*float**,* *optional*) – side ‘a’ length. Defaults to None
        - **b** (*float**,* *optional*) – side ‘b’ length. Defaults to None
        - **c** (*float**,* *optional*) – side ‘c’ length. Defaults to None
        - **A** (*float**,* *optional*) – interior angle ‘A’. Defaults to None
        - **B** (*float**,* *optional*) – interior angle ‘B’. Defaults to None
        - **C** (*float**,* *optional*) – interior angle ‘C’. Defaults to None
        - **rotation** (*float**,* *optional*) – angle to rotate object. Defaults to 0
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]**,* *optional*) – align MIN, CENTER, or MAX of object.
          Defaults to None
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

    Raises:
    :   **ValueError** – One length and two other values were not provided

    A
    :   interior angle ‘A’ in degrees

    B
    :   interior angle ‘B’ in degrees

    C
    :   interior angle ‘C’ in degrees

    a
    :   length of side ‘a’

    b
    :   length of side ‘b’

    c
    :   length of side ‘c’

    edge\_a
    :   edge ‘a’

    edge\_b
    :   edge ‘b’

    edge\_c
    :   edge ‘c’

    vertex\_A
    :   vertex ‘A’

    vertex\_B
    :   vertex ‘B’

    vertex\_C
    :   vertex ‘C’

## 3D Objects

[`Box`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Box "objects_part.Box")  *(for structural beams — UPN / IPN / UPE / flat bars — see `bd_beams_and_bars` (install manually, requires Python 3.13+))*

![_images/box_example.svg](https://build123d.readthedocs.io/en/latest/_images/box_example.svg)

Box defined by length, width, height

[`Cone`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Cone "objects_part.Cone")

![_images/cone_example.svg](https://build123d.readthedocs.io/en/latest/_images/cone_example.svg)

Cone defined by radii and height

[`ConvexPolyhedron`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.ConvexPolyhedron "objects_part.ConvexPolyhedron")

![_images/convex_polyhedron_example.svg](https://build123d.readthedocs.io/en/latest/_images/convex_polyhedron_example.svg)

Convex Polyhedron defined by points

[`CounterBoreHole`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.CounterBoreHole "objects_part.CounterBoreHole")  *(see also: threaded fastener variants via `bd_warehouse.fastener`)*

![_images/counter_bore_hole_example.svg](https://build123d.readthedocs.io/en/latest/_images/counter_bore_hole_example.svg)

Counter bore hole defined by radii and depths

[`CounterSinkHole`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.CounterSinkHole "objects_part.CounterSinkHole")  *(see also: threaded fastener variants via `bd_warehouse.fastener`)*

![_images/counter_sink_hole_example.svg](https://build123d.readthedocs.io/en/latest/_images/counter_sink_hole_example.svg)

Counter sink hole defined by radii and depth and angle

[`Cylinder`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Cylinder "objects_part.Cylinder")  *(for threaded shafts / rods, prefer `bd_warehouse.thread.IsoThread` over a plain cylinder)*

![_images/cylinder_example.svg](https://build123d.readthedocs.io/en/latest/_images/cylinder_example.svg)

Cylinder defined by radius and height

[`Hole`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Hole "objects_part.Hole")  *(helical threaded holes available via `bd_warehouse.thread`)*

![_images/hole_example.svg](https://build123d.readthedocs.io/en/latest/_images/hole_example.svg)

Hole defined by radius and depth

[`Sphere`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Sphere "objects_part.Sphere")  *(bearings and spherical fasteners live in `bd_warehouse.bearing` / `.fastener`)*

![_images/sphere_example.svg](https://build123d.readthedocs.io/en/latest/_images/sphere_example.svg)

Sphere defined by radius and arc angles

[`Torus`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Torus "objects_part.Torus")  *(for involute gears, use `py_gearworks` rather than approximating with a torus)*

![_images/torus_example.svg](https://build123d.readthedocs.io/en/latest/_images/torus_example.svg)

Torus defined major and minor radii

[`Wedge`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.Wedge "objects_part.Wedge")

![_images/wedge_example.svg](https://build123d.readthedocs.io/en/latest/_images/wedge_example.svg)

Wedge defined by lengths along multiple Axes

### Reference

*class* BasePartObject(*part: ~build123d.topology.composite.Part | ~build123d.topology.three\_d.Solid*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Base class for all BuildPart objects & operations

    Parameters:
    :   - **solid** ([*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid")) – object to create
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to None
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD

*class* Box(*length: float*, *width: float*, *height: float*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: Box

    Create a box defined by length, width, and height.

    Parameters:
    :   - **length** (*float*) – box length
        - **width** (*float*) – box width
        - **height** (*float*) – box height
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to (Align.CENTER, Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

*class* Cone(*bottom\_radius: float*, *top\_radius: float*, *height: float*, *arc\_size: float = 360*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: Cone

    Create a cone defined by bottom radius, top radius, and height.

    Parameters:
    :   - **bottom\_radius** (*float*) – bottom radius
        - **top\_radius** (*float*) – top radius, may be zero
        - **height** (*float*) – cone height
        - **arc\_size** (*float**,* *optional*) – angular size of cone. Defaults to 360
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to (Align.CENTER, Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

*class* ConvexPolyhedron(*points: ~collections.abc.Iterable[~build123d.geometry.Vector | tuple[float, float] | tuple[float, float, float] | ~collections.abc.Sequence[float]], rotation: ~build123d.geometry.Rotation | tuple[float, float, float] = (0, 0, 0), align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align, ~build123d.build\_enums.Align, ~build123d.build\_enums.Align] | None = <Align.NONE>, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: ConvexPolyhedron

    Create a convex solid from the convex hull of the provided points.

    Parameters:
    :   - **points** (*Iterable**[**VectorLike**]*) – vertices of the polyhedron
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to Align.NONE
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

*class* CounterBoreHole(*radius: float*, *counter\_bore\_radius: float*, *counter\_bore\_depth: float*, *depth: float | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.SUBTRACT>*)
:   Part Operation: Counter Bore Hole

    Create a counter bore hole defined by radius, counter bore radius, counter bore and depth.

    Parameters:
    :   - **radius** (*float*) – hole radius
        - **counter\_bore\_radius** (*float*) – counter bore radius
        - **counter\_bore\_depth** (*float*) – counter bore depth
        - **depth** (*float**,* *optional*) – hole depth, through part if None. Defaults to None
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.SUBTRACT

*class* CounterSinkHole(*radius: float*, *counter\_sink\_radius: float*, *depth: float | None = None*, *counter\_sink\_angle: float = 82*, *mode: ~build123d.build\_enums.Mode = <Mode.SUBTRACT>*)
:   Part Operation: Counter Sink Hole

    Create a countersink hole defined by radius, countersink radius, countersink
    angle, and depth.

    Parameters:
    :   - **radius** (*float*) – hole radius
        - **counter\_sink\_radius** (*float*) – countersink radius
        - **depth** (*float**,* *optional*) – hole depth, through part if None. Defaults to None
        - **counter\_sink\_angle** (*float**,* *optional*) – cone angle. Defaults to 82
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.SUBTRACT

*class* Cylinder(*radius: float*, *height: float*, *arc\_size: float = 360*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: Cylinder

    Create a cylinder defined by radius and height.

    Parameters:
    :   - **radius** (*float*) – cylinder radius
        - **height** (*float*) – cylinder height
        - **arc\_size** (*float**,* *optional*) – angular size of cone. Defaults to 360.
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to (Align.CENTER, Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

*class* Hole(*radius: float*, *depth: float | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.SUBTRACT>*)
:   Part Operation: Hole

    Create a hole defined by radius and depth.

    Parameters:
    :   - **radius** (*float*) – hole radius
        - **depth** (*float**,* *optional*) – hole depth, through part if None. Defaults to None
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.SUBTRACT

*class* Sphere(*radius: float*, *arc\_size1: float = -90*, *arc\_size2: float = 90*, *arc\_size3: float = 360*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: Sphere

    Create a sphere defined by a radius.

    Parameters:
    :   - **radius** (*float*) – sphere radius
        - **arc\_size1** (*float**,* *optional*) – angular size of bottom hemisphere. Defaults to -90.
        - **arc\_size2** (*float**,* *optional*) – angular size of top hemisphere. Defaults to 90.
        - **arc\_size3** (*float**,* *optional*) – angular revolution about pole. Defaults to 360.
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to (Align.CENTER, Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

*class* Torus(*major\_radius: float*, *minor\_radius: float*, *minor\_start\_angle: float = 0*, *minor\_end\_angle: float = 360*, *major\_angle: float = 360*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: Torus

    Create a torus defined by major and minor radii.

    Parameters:
    :   - **major\_radius** (*float*) – major torus radius
        - **minor\_radius** (*float*) – minor torus radius
        - **minor\_start\_angle** (*float**,* *optional*) – angle to start minor arc. Defaults to 0
        - **minor\_end\_angle** (*float**,* *optional*) – angle to end minor arc. Defaults to 360
        - **major\_angle** (*float**,* *optional*) – angle to revolve minor arc. Defaults to 360
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to (Align.CENTER, Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

*class* Wedge(*xsize: float*, *ysize: float*, *zsize: float*, *xmin: float*, *zmin: float*, *xmax: float*, *zmax: float*, *rotation: ~build123d.geometry.Rotation | tuple[float*, *float*, *float] = (0*, *0*, *0)*, *align: ~build123d.build\_enums.Align | tuple[~build123d.build\_enums.Align*, *~build123d.build\_enums.Align*, *~build123d.build\_enums.Align] = (<Align.CENTER>*, *<Align.CENTER>*, *<Align.CENTER>)*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*)
:   Part Object: Wedge

    Create a wedge with a near face defined by xsize and z size, a far face defined by
    xmin to xmax and zmin to zmax, and a depth of ysize.

    Parameters:
    :   - **xsize** (*float*) – length of near face along x-axis
        - **ysize** (*float*) – length of part along y-axis
        - **zsize** (*float*) – length of near face z-axis
        - **xmin** (*float*) – minimum position far face along x-axis
        - **zmin** (*float*) – minimum position far face along z-axis
        - **xmax** (*float*) – maximum position far face along x-axis
        - **zmax** (*float*) – maximum position far face along z-axis
        - **rotation** (*RotationLike**,* *optional*) – angles to rotate about axes. Defaults to (0, 0, 0)
        - **align** ([*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align") *|* *tuple**[*[*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*,* [*Align*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Align "build_enums.Align")*]* *|* *None**,* *optional*) – align MIN, CENTER,
          or MAX of object. Defaults to (Align.CENTER, Align.CENTER, Align.CENTER)
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combine mode. Defaults to Mode.ADD

## Text

### Create Text Object

Create text object or add to `BuildSketch` using [`Text`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Text "objects_sketch.Text"):

[![_images/text.png](https://build123d.readthedocs.io/en/latest/_images/text.png)](https://build123d.readthedocs.io/en/latest/_images/text.png)

```python
```build123d
text = "The quick brown fox jumped over the lazy dog."
Text(text, 10)
```

Specify font and style. Fonts have up to 4 font styles: `REGULAR`, `BOLD`,
`ITALIC`, `BOLDITALIC`. All fonts can use `ITALIC` even if only
`REGULAR` is defined.

```python
```build123d
Text(text, 10, "Arial", font_style=FontStyle.BOLD)
```

Find available fonts on system and available styles:

```python
```build123d
from pprint import pprint
pprint(available_fonts())
```

```python
```text
[
 ...
 Font(name='Arial', styles=('REGULAR', 'BOLD', 'BOLDITALIC', 'ITALIC')),
 Font(name='Arial Black', styles=('REGULAR',)),
 Font(name='Arial Narrow', styles=('REGULAR', 'BOLD', 'BOLDITALIC', 'ITALIC')),
 Font(name='Arial Rounded MT Bold', styles=('REGULAR',)),
 ...
]
```

Font faces like `"Arial Black"` or `"Arial Narrow"` must be specified
by name rather than `FontStyle`:

```python
```build123d
Text(text, 10, "Arial Black")
```

Specify a font file directly by filename:

```python
```build123d
Text(text, 10, font_path="DejaVuSans.ttf")
```

Fonts added via `font_path` persist in the font list:

```python
```build123d
Text(text, 10, font_path="SourceSans3-VariableFont_wght.ttf")
pprint([f.name for f in available_fonts() if "Source Sans" in f.name])
Text(text, 10, "Source Sans 3 Medium")
```

```python
```text
['Source Sans 3',
 'Source Sans 3 Black',
 'Source Sans 3 ExtraBold',
 'Source Sans 3 ExtraLight',
 ...]
```

Add a font file to `FontManager` if a font is reused in the script or
contains multiple font faces:

```python
```build123d
new_font_faces = FontManager().register_font("Roboto-VariableFont_wdth,wght.ttf")
pprint(new_font_faces)
Text(text, 10, "Roboto")
Text(text, 10, "Roboto Black")
```

```python
```text
['Roboto Thin',
 'Roboto ExtraLight',
 'Roboto Light',
 'Roboto',
  ...]
```

### Placement

Multiline text has two methods of alignment.
`text_align` aligns the text relative to its `Location`:

[![_images/text_align.png](https://build123d.readthedocs.io/en/latest/_images/text_align.png)](https://build123d.readthedocs.io/en/latest/_images/text_align.png)

```python
```build123d
Text(text, 10, text_align=(TextAlign.LEFT, TextAlign.TOPFIRSTLINE))
```

`align` aligns the object bounding box relative to its `Location` *after*
text alignment:

[![_images/align.png](https://build123d.readthedocs.io/en/latest/_images/align.png)](https://build123d.readthedocs.io/en/latest/_images/align.png)

```python
```build123d
text = "The quick brown\nfox jumped over\nthe lazy dog."
Text(text, 10, align=(Align.MIN, Align.MIN))
```

Place text along an `Edge` or `Wire` with `path` and `position_on_path`:

[![_images/path.png](https://build123d.readthedocs.io/en/latest/_images/path.png)](https://build123d.readthedocs.io/en/latest/_images/path.png)

```python
```build123d
text = "The quick brown fox"
path = RadiusArc((-50, 0), (50, 0), 100)
Text(
    text,
    10,
    path=path,
    position_on_path=.5,
    text_align=(TextAlign.CENTER, TextAlign.BOTTOM)
)
```

### Single Line Fonts

`"singleline"` is a special font referencing `Relief SingleLine CAD`.
Glyphs are represented as single lines rather than filled faces.

`Text` creates an outlined face by default. The outline width is controlled
by `single_line_width`. This operation is slow with many glyphs.

[![_images/outline.png](https://build123d.readthedocs.io/en/latest/_images/outline.png)](https://build123d.readthedocs.io/en/latest/_images/outline.png)

```python
```build123d
Text(text, 10, "singleline")
Text(text, 10, "singleline", single_line_width=1)
```

Use `Compound.make_text()` to create *unoutlined* single-line text.
Useful for routing, engraving, or drawing label paths.

[![_images/singleline.png](https://build123d.readthedocs.io/en/latest/_images/singleline.png)](https://build123d.readthedocs.io/en/latest/_images/singleline.png)

```python
```build123d
Compound.make_text(text, 10, "singleline")
```

### Common Issues

#### Missing Glyphs or Invalid Geometry

Modern variable-width fonts often contain glyphs with overlapping stroke
outlines, which produce invalid geometry. `ocp_vscode` ignores invalid
faces.

![_images/missing_glyph.png](https://build123d.readthedocs.io/en/latest/_images/missing_glyph.png)

```python
```build123d
Text("The", 10, "Source Sans 3 Black")
```

#### FileNotFoundError

Ensure relative `font_path` specifications are relative to the *current
working directory*.

## Custom Objects

All of the objects presented above were created using one of three base object classes:
[`BaseLineObject`](https://build123d.readthedocs.io/en/latest/objects.html#objects_curve.BaseLineObject "objects_curve.BaseLineObject") , [`BaseSketchObject`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.BaseSketchObject "objects_sketch.BaseSketchObject") , and
[`BasePartObject`](https://build123d.readthedocs.io/en/latest/objects.html#objects_part.BasePartObject "objects_part.BasePartObject") . Users can use these base object classes to
easily create custom objects that have all the functionality of the core objects.

![_images/card_box.svg](https://build123d.readthedocs.io/en/latest/_images/card_box.svg)

Here is an example of a custom sketch object specially created as part of the design of
this playing card storage box ([`see the playing_cards.py example`](https://build123d.readthedocs.io/en/latest/_downloads/151f59a8b3667ffadd50f62e9e000194/playing_cards.py)):

```python
```build123d
class Club(BaseSketchObject):
    def __init__(
        self,
        height: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ):
        with BuildSketch() as club:
            with BuildLine():
                l0 = Line((0, -188), (76, -188))
                b0 = Bezier(l0 @ 1, (61, -185), (33, -173), (17, -81))
                b1 = Bezier(b0 @ 1, (49, -128), (146, -145), (167, -67))
                b2 = Bezier(b1 @ 1, (187, 9), (94, 52), (32, 18))
                b3 = Bezier(b2 @ 1, (92, 57), (113, 188), (0, 188))
                mirror(about=Plane.YZ)
            make_face()
            scale(by=height / club.sketch.bounding_box().size.Y)
        super().__init__(obj=club.sketch, rotation=rotation, align=align, mode=mode)
```

Here the new custom object class is called `Club` and it’s a sub-class of
[`BaseSketchObject`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.BaseSketchObject "objects_sketch.BaseSketchObject") . The `__init__` method contains all
of the parameters used to instantiate the custom object, specially a `height`,
`rotation`, `align`, and `mode` - your objects may contain a sub or super set of
these parameters but should always contain a `mode` parameter such that it
can be combined with a builder’s object.

Next is the creation of the object itself, in this case a sketch of the club suit.

The final line calls the `__init__` method of the super class - i.e.
[`BaseSketchObject`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.BaseSketchObject "objects_sketch.BaseSketchObject") with its parameters.

That’s it, now the `Club` object can be used anywhere a [`Circle`](https://build123d.readthedocs.io/en/latest/objects.html#objects_sketch.Circle "objects_sketch.Circle")
would be used - with either the Algebra or Builder API.

![_images/buildline_example_6.svg](https://build123d.readthedocs.io/en/latest/_images/buildline_example_6.svg)


## External library extensions

These capabilities are not part of the stock build123d `objects` module but are importable alongside it when the harness is installed. Use them only when the task genuinely calls for them; prefer stock primitives otherwise.

- **Extrude** — *(V-slot aluminum extrusion profiles available via `bd_vslot`)*
