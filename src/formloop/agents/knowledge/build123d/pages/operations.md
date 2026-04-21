# Operations

_Source: [https://build123d.readthedocs.io/en/latest/operations.html](https://build123d.readthedocs.io/en/latest/operations.html)_

_Part of the Build123D knowledge pack (formloop/src/formloop/agents/knowledge/build123d/pages/operations.md)._

---

# Operations

Operations are functions that take objects as inputs and transform them into new objects. For example, a 2D Sketch can be extruded to create a 3D Part. All operations are Python functions which can be applied using both the Algebra and Builder APIs. It’s important to note that objects created by operations are not affected by `Locations`, meaning their position is determined solely by the input objects used in the operation.

Here are a couple ways to use [`extrude()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.extrude "operations_part.extrude"), in Builder and Algebra mode:

```python
```build123d
with BuildPart() as cylinder:
    with BuildSketch():
        Circle(radius)
    extrude(amount=height)
```

```python
```build123d
cylinder = extrude(Circle(radius), amount=height)
```

The following table summarizes all of the available operations. Operations marked as 1D are
applicable to BuildLine and Algebra Curve, 2D to BuildSketch and Algebra Sketch, 3D to
BuildPart and Algebra Part.

| Operation | Description | 0D | 1D | 2D | 3D | Example |
| --- | --- | --- | --- | --- | --- | --- |
| [`add()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.add "operations_generic.add") | Add object to builder |  | ✓ | ✓ | ✓ | [16](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-16) |
| [`bounding_box()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.bounding_box "operations_generic.bounding_box") | Add bounding box as Shape |  | ✓ | ✓ | ✓ |  |
| [`chamfer()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.chamfer "operations_generic.chamfer") | Bevel Vertex or Edge |  |  | ✓ | ✓ | [9](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-9) |
| [`draft()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.draft "operations_part.draft") | Add a draft taper to a part |  |  |  | ✓ | [Cast Bearing Unit](https://build123d.readthedocs.io/en/latest/examples_1.html#examples-cast-bearing-unit) |
| [`extrude()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.extrude "operations_part.extrude") | Draw 2D Shape into 3D |  |  |  | ✓ | [3](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-3) |
| [`fillet()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.fillet "operations_generic.fillet") | Radius Vertex or Edge |  |  | ✓ | ✓ | [9](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-9) |
| [`full_round()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_sketch.full_round "operations_sketch.full_round") | Round-off Face along given Edge |  |  | ✓ |  | [24-SPO-06 Buffer Stand](https://build123d.readthedocs.io/en/latest/tttt.html#ttt-24-spo-06) |
| [`loft()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.loft "operations_part.loft") | Create 3D Shape from sections |  |  |  | ✓ | [24](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-24) |
| [`make_brake_formed()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.make_brake_formed "operations_part.make_brake_formed") | Create sheet metal parts |  |  |  | ✓ |  |
| [`make_face()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_sketch.make_face "operations_sketch.make_face") | Create a Face from Edges |  |  | ✓ |  | [4](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-4) |
| [`make_hull()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_sketch.make_hull "operations_sketch.make_hull") | Create Convex Hull from Edges |  |  | ✓ |  |  |
| [`mirror()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.mirror "operations_generic.mirror") | Mirror about Plane |  | ✓ | ✓ | ✓ | [15](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-15) |
| [`offset()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.offset "operations_generic.offset") | Inset or outset Shape |  | ✓ | ✓ | ✓ | [25](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-25) |
| [`project()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.project "operations_generic.project") | Project points, lines or Faces | ✓ | ✓ | ✓ |  |  |
| [`project_workplane()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.project_workplane "operations_part.project_workplane") | Create workplane for projection |  |  |  |  |  |
| [`revolve()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.revolve "operations_part.revolve") | Swing 2D Shape about Axis |  |  |  | ✓ | [23](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-23) |
| [`scale()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.scale "operations_generic.scale") | Change size of Shape |  | ✓ | ✓ | ✓ |  |
| [`section()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.section "operations_part.section") | Generate 2D slices from 3D Shape |  |  |  | ✓ |  |
| [`split()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.split "operations_generic.split") | Divide object by Plane |  | ✓ | ✓ | ✓ | [27](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-27) |
| [`sweep()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_generic.sweep "operations_generic.sweep") | Extrude 1/2D section(s) along path |  |  | ✓ | ✓ | [14](https://build123d.readthedocs.io/en/latest/introductory_examples.html#ex-14) |
| [`thicken()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_part.thicken "operations_part.thicken") | Expand 2D section(s) |  |  |  | ✓ |  |
| [`trace()`](https://build123d.readthedocs.io/en/latest/operations.html#operations_sketch.trace "operations_sketch.trace") | Convert lines to faces |  |  | ✓ |  |  |

The following table summarizes all of the selectors that can be used within
the scope of a Builder. Note that they will extract objects from the builder that is
currently within scope without it being explicitly referenced.

|  | | Builder | | |
| --- | --- | --- | --- | --- |
| Selector | Description | Line | Sketch | Part |
| [`edge()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.edge "build_common.edge") | Select edge from current builder | ✓ | ✓ | ✓ |
| [`edges()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.edges "build_common.edges") | Select edges from current builder | ✓ | ✓ | ✓ |
| [`face()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.face "build_common.face") | Select face from current builder |  | ✓ | ✓ |
| [`faces()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.faces "build_common.faces") | Select faces from current builder |  | ✓ | ✓ |
| [`solid()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.solid "build_common.solid") | Select solid from current builder |  |  | ✓ |
| [`solids()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.solids "build_common.solids") | Select solids from current builder |  |  | ✓ |
| [`vertex()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.vertex "build_common.vertex") | Select vertex from current builder | ✓ | ✓ | ✓ |
| [`vertices()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.vertices "build_common.vertices") | Select vertices from current builder | ✓ | ✓ | ✓ |
| [`wire()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.wire "build_common.wire") | Select wire from current builder | ✓ | ✓ | ✓ |
| [`wires()`](https://build123d.readthedocs.io/en/latest/operations.html#build_common.wires "build_common.wires") | Select wires from current builder | ✓ | ✓ | ✓ |

## Reference

add(*objects: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid | ~build123d.topology.composite.Compound | ~build123d.build\_common.Builder | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid | ~build123d.topology.composite.Compound | ~build123d.build\_common.Builder], rotation: float | ~build123d.geometry.Rotation | tuple[float, float, float] | None = None, clean: bool = True, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Compound
:   Generic Object: Add Object to Part or Sketch

    Add an object to a builder.

    BuildPart:
    :   Edges and Wires are added to pending\_edges. Compounds of Face are added to
        pending\_faces. Solids or Compounds of Solid are combined into the part.

    BuildSketch:
    :   Edges and Wires are added to pending\_edges. Compounds of Face are added to sketch.

    BuildLine:
    :   Edges and Wires are added to line.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid") *|* [*Compound*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Compound "topology.Compound") *or* *Iterable of*) – objects to add
        - **rotation** (*float* *|* *RotationLike**,* *optional*) – rotation angle for sketch,
          rotation about each axis for part. Defaults to None.
        - **clean** – Remove extraneous internal structure. Defaults to True.

bounding\_box(*objects: ~build123d.topology.shape\_core.Shape | ~collections.abc.Iterable[~build123d.topology.shape\_core.Shape] | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.PRIVATE>*) → Sketch | Part
:   Generic Operation: Add Bounding Box

    Applies to: BuildSketch and BuildPart

    Add the 2D or 3D bounding boxes of the object sequence

    Parameters:
    :   - **objects** ([*Shape*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape "topology.Shape") *or* *Iterable of*) – objects to create bbox for
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

chamfer(*objects: Edge | Vertex | Iterable[Edge | Vertex]*, *length: float*, *length2: float | None = None*, *angle: float | None = None*, *reference: Edge | Face | None = None*) → Sketch | Part
:   Generic Operation: chamfer

    Applies to 2 and 3 dimensional objects.

    Chamfer the given sequence of edges or vertices.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex") *or* *Iterable of*) – edges or vertices to chamfer
        - **length** (*float*) – chamfer size
        - **length2** (*float**,* *optional*) – asymmetric chamfer size. Defaults to None.
        - **angle** (*float**,* *optional*) – chamfer angle in degrees. Defaults to None.
        - **reference** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")) – identifies the side where length is measured. Edge(s) must
          be part of the face. Vertex/Vertices must be part of edge

    Raises:
    :   - **ValueError** – no objects provided
        - **ValueError** – objects must be Edges
        - **ValueError** – objects must be Vertices
        - **ValueError** – Only one of length2 or angle should be provided
        - **ValueError** – reference can only be used in conjunction with length2 or angle

draft(*faces: Face | Iterable[Face]*, *neutral\_plane: Plane*, *angle: float*) → Part
:   Part Operation: draft

    Apply a draft angle to the given faces of the part

    Parameters:
    :   - **faces** – Faces to which the draft should be applied.
        - **neutral\_plane** – Plane defining the neutral direction and position.
        - **angle** – Draft angle in degrees.

extrude(*to\_extrude: ~build123d.topology.two\_d.Face | ~build123d.topology.composite.Sketch | None = None*, *amount: float | None = None*, *dir: ~build123d.geometry.Vector | tuple[float*, *float] | tuple[float*, *float*, *float] | ~collections.abc.Sequence[float] | None = None*, *until: ~build123d.build\_enums.Until | None = None*, *target: ~build123d.topology.three\_d.Solid | ~build123d.topology.composite.Compound | None = None*, *both: bool = False*, *taper: float = 0.0*, *clean: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Part
:   Part Operation: extrude

    Extrude a sketch or face by an amount or until another object.

    Parameters:
    :   - **to\_extrude** (*Union**[*[*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")*,* [*Sketch*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Sketch "topology.Sketch")*]**,* *optional*) – object to extrude. Defaults to None.
        - **amount** (*float**,* *optional*) – distance to extrude, sign controls direction. Defaults to None.
        - **dir** (*VectorLike**,* *optional*) – direction. Defaults to None.
        - **until** ([*Until*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Until "build_enums.Until")*,* *optional*) – extrude limit. Defaults to None.
        - **target** ([*Shape*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape "topology.Shape")*,* *optional*) – extrude until target. Defaults to None.
        - **both** (*bool**,* *optional*) – extrude in both directions. Defaults to False.
        - **taper** (*float**,* *optional*) – taper angle. Defaults to 0.0.
        - **clean** (*bool**,* *optional*) – Remove extraneous internal structure. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   - **ValueError** – No object to extrude
        - **ValueError** – No target object

    Returns:
    :   extruded object

    Return type:
    :   [*Part*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Part "topology.Part")

fillet(*objects: Edge | Vertex | Iterable[Edge | Vertex]*, *radius: float*) → Sketch | Part | Curve
:   Generic Operation: fillet

    Applies to 2 and 3 dimensional objects.

    Fillet the given sequence of edges or vertices. Note that vertices on
    either end of an open line will be automatically skipped.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex") *or* *Iterable of*) – edges or vertices to fillet
        - **radius** (*float*) – fillet size - must be less than 1/2 local width

    Raises:
    :   - **ValueError** – no objects provided
        - **ValueError** – objects must be Edges
        - **ValueError** – objects must be Vertices
        - **ValueError** – nothing to fillet

full\_round(*edge: ~build123d.topology.one\_d.Edge*, *invert: bool = False*, *voronoi\_point\_count: int = 100*, *mode: ~build123d.build\_enums.Mode = <Mode.REPLACE>*) → tuple[Sketch, Vector, float]
:   Sketch Operation: full\_round

    Given an edge from a Face/Sketch, modify the face by replacing the given edge with the
    arc of the Voronoi largest empty circle that will fit within the Face. This
    “rounds off” the end of the object.

    Parameters:
    :   - **edge** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")) – target Edge to remove
        - **invert** (*bool**,* *optional*) – make the arc concave instead of convex. Defaults to False.
        - **voronoi\_point\_count** (*int**,* *optional*) – number of points along each edge
          used to create the voronoi vertices as potential locations for the
          center of the largest empty circle. Defaults to 100.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.REPLACE.

    Raises:
    :   **ValueError** – Invalid geometry

    Returns:
    :   the modified shape

    Return type:
    :   [*Sketch*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Sketch "topology.Sketch")

loft(*sections: ~build123d.topology.two\_d.Face | ~build123d.topology.composite.Sketch | ~collections.abc.Iterable[~build123d.topology.zero\_d.Vertex | ~build123d.topology.two\_d.Face | ~build123d.topology.composite.Sketch] | None = None*, *ruled: bool = False*, *clean: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Part
:   Part Operation: loft

    Loft the pending sketches/faces, across all workplanes, into a solid.

    Parameters:
    :   - **sections** ([*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex")*,* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")*,* [*Sketch*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Sketch "topology.Sketch")) – slices to loft into object. If not provided, pending\_faces
          will be used. If vertices are to be used, a vertex can be the first, last, or
          first and last elements.
        - **ruled** (*bool**,* *optional*) – discontiguous layer tangents. Defaults to False.
        - **clean** (*bool**,* *optional*) – Remove extraneous internal structure. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

make\_brake\_formed(*thickness: float, station\_widths: float | ~collections.abc.Iterable[float], line: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.composite.Curve | None = None, side: ~build123d.build\_enums.Side = <Side.LEFT>, kind: ~build123d.build\_enums.Kind = <Kind.ARC>, clean: bool = True, mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Part
:   Create a part typically formed with a sheet metal brake from a single outline.
    The line parameter describes how the material is to be bent. Either a single
    width value or a width value at each vertex or station is provided to control
    the width of the end part. Note that if multiple values are provided there
    must be one for each vertex and that the resulting part is composed of linear
    segments.

    Parameters:
    :   - **thickness** (*float*) – sheet metal thickness
        - **station\_widths** (*Union**[**float**,* *Iterable**[**float**]**]*) – width of part at
          each vertex or a single value. Note that this width is perpendicular
          to the provided line/plane.
        - **line** (*Union**[*[*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")*,* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")*,* [*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve")*]**,* *optional*) – outline of part. Defaults to None.
        - **side** (*Side**,* *optional*) – offset direction. Defaults to Side.LEFT.
        - **kind** ([*Kind*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Kind "build_enums.Kind")*,* *optional*) – offset intersection type. Defaults to Kind.ARC.
        - **clean** (*bool**,* *optional*) – clean the resulting solid. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   - **ValueError** – invalid line type
        - **ValueError** – not line provided
        - **ValueError** – line not suitable
        - **ValueError** – incorrect # of width values

    Returns:
    :   sheet metal part

    Return type:
    :   [*Part*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Part "topology.Part")

make\_face(*edges: ~build123d.topology.one\_d.Edge | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge] | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Sketch
:   Sketch Operation: make\_face

    Create a face from the given perimeter edges.

    Parameters:
    :   - **edges** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")) – sequence of perimeter edges. Defaults to all
          sketch pending edges.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

make\_hull(*edges: ~build123d.topology.one\_d.Edge | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge] | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Sketch
:   Sketch Operation: make\_hull

    Create a face from the convex hull of the given edges

    Parameters:
    :   - **edges** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")*,* *optional*) – sequence of edges to hull. Defaults to all
          sketch pending edges.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

mirror(*objects: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.composite.Compound | ~build123d.topology.composite.Curve | ~build123d.topology.composite.Sketch | ~build123d.topology.composite.Part | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.composite.Compound | ~build123d.topology.composite.Curve | ~build123d.topology.composite.Sketch | ~build123d.topology.composite.Part] | None = None*, *about: ~build123d.geometry.Plane = Plane((0*, *0*, *0)*, *(1*, *0*, *0)*, *(0*, *-1*, *0))*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Curve | Sketch | Part | Compound
:   Generic Operation: mirror

    Applies to 1, 2, and 3 dimensional objects.

    Mirror a sequence of objects over the given plane.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Compound*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Compound "topology.Compound") *or* *Iterable of*) – objects to mirror
        - **about** ([*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane")*,* *optional*) – reference plane. Defaults to “XZ”.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   **ValueError** – missing objects

offset(*objects: ~build123d.topology.one\_d.Edge | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid | ~build123d.topology.composite.Compound | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid | ~build123d.topology.composite.Compound] | None = None*, *amount: float = 0*, *openings: ~build123d.topology.two\_d.Face | list[~build123d.topology.two\_d.Face] | None = None*, *kind: ~build123d.build\_enums.Kind = <Kind.ARC>*, *side: ~build123d.build\_enums.Side = <Side.BOTH>*, *closed: bool = True*, *min\_edge\_length: float | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.REPLACE>*) → Curve | Sketch | Part | Compound
:   Generic Operation: offset

    Applies to 1, 2, and 3 dimensional objects.

    Offset the given sequence of Edges, Faces, Compound of Faces, or Solids.
    The kind parameter controls the shape of the transitions. For Solid
    objects, the openings parameter allows selected faces to be open, like
    a hollow box with no lid.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid") *|* [*Compound*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Compound "topology.Compound") *or* *Iterable of*) – objects to offset
        - **amount** (*float*) – positive values external, negative internal
        - **openings** (*list**[*[*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")*]**,* *optional*) – Defaults to None.
        - **kind** ([*Kind*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Kind "build_enums.Kind")*,* *optional*) – transition shape. Defaults to Kind.ARC.
        - **side** (*Side**,* *optional*) – side to place offset. Defaults to Side.BOTH.
        - **closed** (*bool**,* *optional*) – if Side!=BOTH, close the LEFT or RIGHT
          offset. Defaults to True.
        - **min\_edge\_length** (*float**,* *optional*) – repair degenerate edges generated by offset
          by eliminating edges of minimum length in offset wire. Defaults to None.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.REPLACE.

    Raises:
    :   - **ValueError** – missing objects
        - **ValueError** – Invalid object type

project(*objects: ~build123d.topology.one\_d.Edge | ~build123d.topology.two\_d.Face | ~build123d.topology.one\_d.Wire | ~build123d.geometry.Vector | ~build123d.topology.zero\_d.Vertex | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge | ~build123d.topology.two\_d.Face | ~build123d.topology.one\_d.Wire | ~build123d.geometry.Vector | ~build123d.topology.zero\_d.Vertex] | None = None*, *workplane: ~build123d.geometry.Plane | None = None*, *target: ~build123d.topology.three\_d.Solid | ~build123d.topology.composite.Compound | ~build123d.topology.composite.Part | None = None*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Curve | Sketch | Compound | ShapeList[Vector]
:   Generic Operation: project

    Applies to 0, 1, and 2 dimensional objects.

    Project the given objects or points onto a BuildLine or BuildSketch workplane in
    the direction of the normal of that workplane. When projecting onto a
    sketch a Face(s) are generated while Edges are generated for BuildLine.
    Will only use the first if BuildSketch has multiple active workplanes.
    In algebra mode a workplane must be provided and the output is either
    a Face, Curve, Sketch, Compound, or ShapeList[Vector].

    Note that only if mode is not Mode.PRIVATE only Faces can be projected into
    BuildSketch and Edge/Wires into BuildLine.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire") *|* *VectorLike* *|* [*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex") *or* *Iterable of*) – objects or points to project
        - **workplane** ([*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane")*,* *optional*) – screen workplane
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   - **ValueError** – project doesn’t accept group\_by
        - **ValueError** – Either a workplane must be provided or a builder must be active
        - **ValueError** – Points and faces can only be projected in PRIVATE mode
        - **ValueError** – Edges, wires and points can only be projected in PRIVATE mode
        - **RuntimeError** – BuildPart doesn’t have a project operation

project\_workplane(*origin: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float] | Vertex*, *x\_dir: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float] | Vertex*, *projection\_dir: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]*, *distance: float*) → Plane
:   Part Operation: project\_workplane

    Return a plane to be used as a BuildSketch or BuildLine workplane
    with a known origin and x direction. The plane’s origin will be
    the projection of the provided origin (in 3D space). The plane’s
    x direction will be the projection of the provided x\_dir (in 3D space).

    Parameters:
    :   - **origin** (*Union**[**VectorLike**,* [*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex")*]*) – origin in 3D space
        - **x\_dir** (*Union**[**VectorLike**,* [*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex")*]*) – x direction in 3D space
        - **projection\_dir** (*VectorLike*) – projection direction
        - **distance** (*float*) – distance from origin to workplane

    Raises:
    :   - **RuntimeError** – Not suitable for BuildLine or BuildSketch
        - **ValueError** – x\_dir perpendicular to projection\_dir

    Returns:
    :   workplane aligned for projection

    Return type:
    :   [*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane")

revolve(*profiles: ~build123d.topology.two\_d.Face | ~collections.abc.Iterable[~build123d.topology.two\_d.Face] | None = None*, *axis: ~build123d.geometry.Axis = Axis((0*, *0*, *0)*, *(0*, *0*, *1))*, *revolution\_arc: float = 360.0*, *clean: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Part
:   Part Operation: Revolve

    Revolve the profile or pending sketches/face about the given axis.
    Note that the most common use case is when the axis is in the same plane as the
    face to be revolved but this isn’t required.

    Parameters:
    :   - **profiles** ([*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")*,* *optional*) – 2D profile(s) to revolve.
        - **axis** ([*Axis*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Axis "geometry.Axis")*,* *optional*) – axis of rotation. Defaults to Axis.Z.
        - **revolution\_arc** (*float**,* *optional*) – angular size of revolution. Defaults to 360.0.
        - **clean** (*bool**,* *optional*) – Remove extraneous internal structure. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   **ValueError** – Invalid axis of revolution

scale(*objects: ~build123d.topology.shape\_core.Shape | ~collections.abc.Iterable[~build123d.topology.shape\_core.Shape] | None = None*, *by: float | tuple[float*, *float*, *float] = 1*, *mode: ~build123d.build\_enums.Mode = <Mode.REPLACE>*) → Curve | Sketch | Part | Compound
:   Generic Operation: scale

    Applies to 1, 2, and 3 dimensional objects.

    Scale a sequence of objects. Note that when scaling non-uniformly across
    the three axes, the type of the underlying object may change to bspline from
    line, circle, etc.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Compound*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Compound "topology.Compound") *|* [*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid") *or* *Iterable of*) – objects to scale
        - **by** (*float* *|* *tuple**[**float**,* *float**,* *float**]*) – scale factor
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.REPLACE.

    Raises:
    :   **ValueError** – missing objects

section(*obj: ~build123d.topology.composite.Part | None = None*, *section\_by: ~build123d.geometry.Plane | ~collections.abc.Iterable[~build123d.geometry.Plane] = Plane((0*, *0*, *0)*, *(1*, *0*, *0)*, *(0*, *-1*, *0))*, *height: float = 0.0*, *clean: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.PRIVATE>*) → Sketch
:   Part Operation: section

    Slices current part at the given height by section\_by or current workplane(s).

    Parameters:
    :   - **obj** ([*Part*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Part "topology.Part")*,* *optional*) – object to section. Defaults to None.
        - **section\_by** ([*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane")*,* *optional*) – plane(s) to section object.
          Defaults to None.
        - **height** (*float**,* *optional*) – workplane offset. Defaults to 0.0.
        - **clean** (*bool**,* *optional*) – Remove extraneous internal structure. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.INTERSECT.

split(*objects: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid] | None = None*, *bisect\_by: ~build123d.geometry.Plane | ~build123d.topology.two\_d.Face | ~build123d.topology.two\_d.Shell = Plane((0*, *0*, *0)*, *(1*, *0*, *0)*, *(0*, *-1*, *0))*, *keep: ~build123d.build\_enums.Keep = <Keep.TOP>*, *mode: ~build123d.build\_enums.Mode = <Mode.REPLACE>*)
:   Generic Operation: split

    Applies to 1, 2, and 3 dimensional objects.

    Bisect object with plane and keep either top, bottom or both.

    Parameters:
    :   - **objects** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid") *or* *Iterable of*)
        - **bisect\_by** ([*Plane*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Plane "geometry.Plane") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")*,* *optional*) – plane to segment part.
          Defaults to Plane.XZ.
        - **keep** ([*Keep*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Keep "build_enums.Keep")*,* *optional*) – selector for which segment to keep. Defaults to Keep.TOP.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.REPLACE.

    Raises:
    :   **ValueError** – missing objects

sweep(*sections: ~build123d.topology.composite.Compound | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid | ~collections.abc.Iterable[~build123d.topology.composite.Compound | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~build123d.topology.two\_d.Face | ~build123d.topology.three\_d.Solid] | None = None*, *path: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~collections.abc.Iterable[~build123d.topology.one\_d.Edge] | None = None*, *multisection: bool = False*, *is\_frenet: bool = False*, *transition: ~build123d.build\_enums.Transition = <Transition.TRANSFORMED>*, *normal: ~build123d.geometry.Vector | tuple[float*, *float] | tuple[float*, *float*, *float] | ~collections.abc.Sequence[float] | None = None*, *binormal: ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | None = None*, *clean: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Part | Sketch
:   Generic Operation: sweep

    Sweep pending 1D or 2D objects along path.

    Parameters:
    :   - **sections** ([*Compound*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Compound "topology.Compound") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire") *|* [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face") *|* [*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid")) – cross sections to sweep into object
        - **path** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")*,* *optional*) – path to follow.
          Defaults to context pending\_edges.
        - **multisection** (*bool**,* *optional*) – sweep multiple on path. Defaults to False.
        - **is\_frenet** (*bool**,* *optional*) – use frenet algorithm. Defaults to False.
        - **transition** ([*Transition*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Transition "build_enums.Transition")*,* *optional*) – discontinuity handling option.
          Defaults to Transition.TRANSFORMED.
        - **normal** (*VectorLike**,* *optional*) – fixed normal. Defaults to None.
        - **binormal** ([*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")*,* *optional*) – guide rotation along path. Defaults to None.
        - **clean** (*bool**,* *optional*) – Remove extraneous internal structure. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination. Defaults to Mode.ADD.

thicken(*to\_thicken: ~build123d.topology.two\_d.Face | ~build123d.topology.composite.Sketch | None = None*, *amount: float | None = None*, *normal\_override: ~build123d.geometry.Vector | tuple[float*, *float] | tuple[float*, *float*, *float] | ~collections.abc.Sequence[float] | None = None*, *both: bool = False*, *clean: bool = True*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Part
:   Part Operation: thicken

    Create a solid(s) from a potentially non planar face(s) by thickening along the normals.

    Parameters:
    :   - **to\_thicken** (*Union**[*[*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")*,* [*Sketch*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Sketch "topology.Sketch")*]**,* *optional*) – object to thicken. Defaults to None.
        - **amount** (*float*) – distance to extrude, sign controls direction.
        - **normal\_override** ([*Vector*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#geometry.Vector "geometry.Vector")*,* *optional*) – The normal\_override vector can be used to
          indicate which way is ‘up’, potentially flipping the face normal direction
          such that many faces with different normals all go in the same direction
          (direction need only be +/- 90 degrees from the face normal). Defaults to None.
        - **both** (*bool**,* *optional*) – thicken in both directions. Defaults to False.
        - **clean** (*bool**,* *optional*) – Remove extraneous internal structure. Defaults to True.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   - **ValueError** – No object to extrude
        - **ValueError** – No target object

    Returns:
    :   extruded object

    Return type:
    :   [*Part*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Part "topology.Part")

trace(*lines: ~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire | ~collections.abc.Iterable[~build123d.topology.composite.Curve | ~build123d.topology.one\_d.Edge | ~build123d.topology.one\_d.Wire] | None = None*, *line\_width: float = 1*, *mode: ~build123d.build\_enums.Mode = <Mode.ADD>*) → Sketch
:   Sketch Operation: trace

    Convert edges, wires or pending edges into faces by sweeping a perpendicular line along them.

    Parameters:
    :   - **lines** ([*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire") *|* *Iterable**[*[*Curve*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Curve "topology.Curve") *|* [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge") *|* [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")*]**]**,* *optional*) – lines to
          trace. Defaults to sketch pending edges.
        - **line\_width** (*float**,* *optional*) – Defaults to 1.
        - **mode** ([*Mode*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Mode "build_enums.Mode")*,* *optional*) – combination mode. Defaults to Mode.ADD.

    Raises:
    :   **ValueError** – No objects to trace

    Returns:
    :   Traced lines

    Return type:
    :   [*Sketch*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Sketch "topology.Sketch")

edge(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → Edge
:   Return Edge

    Return an edge.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Edge selector. Defaults to Select.ALL.

    Returns:
    :   Edge extracted

    Return type:
    :   [*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")

edges(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → ShapeList[Edge]
:   Return Edges

    Return either all or the edges created during the last operation.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Edge selector. Defaults to Select.ALL.

    Returns:
    :   Edges extracted

    Return type:
    :   [*ShapeList*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList")[[*Edge*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Edge "topology.Edge")]

face(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → Face
:   Return Face

    Return a face.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Face selector. Defaults to Select.ALL.

    Returns:
    :   Face extracted

    Return type:
    :   [*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")

faces(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → ShapeList[Face]
:   Return Faces

    Return either all or the faces created during the last operation.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Face selector. Defaults to Select.ALL.

    Returns:
    :   Faces extracted

    Return type:
    :   [*ShapeList*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList")[[*Face*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Face "topology.Face")]

solid(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → Solid
:   Return Solid

    Return a solid.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Solid selector. Defaults to Select.ALL.

    Returns:
    :   Solid extracted

    Return type:
    :   [*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid")

solids(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → ShapeList[Solid]
:   Return Solids

    Return either all or the solids created during the last operation.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Solid selector. Defaults to Select.ALL.

    Returns:
    :   Solids extracted

    Return type:
    :   [*ShapeList*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList")[[*Solid*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Solid "topology.Solid")]

vertex(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → Vertex
:   Return Vertex

    Return a vertex.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Vertex selector. Defaults to Select.ALL.

    Returns:
    :   Vertex extracted

    Return type:
    :   [*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex")

vertices(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → ShapeList[Vertex]
:   Return Vertices

    Return either all or the vertices created during the last operation.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Vertex selector. Defaults to Select.ALL.

    Returns:
    :   Vertices extracted

    Return type:
    :   [*ShapeList*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList")[[*Vertex*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Vertex "topology.Vertex")]

wire(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → Wire
:   Return Wire

    Return a wire.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Wire selector. Defaults to Select.ALL.

    Returns:
    :   Wire extracted

    Return type:
    :   [*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")

wires(*self*, *select: ~build123d.build\_enums.Select = <Select.ALL>*) → ShapeList[Wire]
:   Return Wires

    Return either all or the wires created during the last operation.

    Parameters:
    :   **select** ([*Select*](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select")*,* *optional*) – Wire selector. Defaults to Select.ALL.

    Returns:
    :   Wires extracted

    Return type:
    :   [*ShapeList*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList")[[*Wire*](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Wire "topology.Wire")]
