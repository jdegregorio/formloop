# Topology Selection and Exploration

_Source: [https://build123d.readthedocs.io/en/latest/topology_selection.html](https://build123d.readthedocs.io/en/latest/topology_selection.html)_

_Part of the Build123D knowledge pack (formloop/src/formloop/agents/knowledge/build123d/pages/topology_selection.md)._

---

# Topology Selection and Exploration

[Topology](https://build123d.readthedocs.io/en/latest/key_concepts.html#topology) is the structure of build123d geometric features and traversing the
topology of a part is often required to specify objects for an operation or to locate a
CAD feature. [Selectors](https://build123d.readthedocs.io/en/latest/topology_selection.html#selectors) allow selection of topology objects into a [`ShapeList`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList").
[Operators](https://build123d.readthedocs.io/en/latest/topology_selection.html#operators) are powerful methods further explore and refine a [`ShapeList`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList") for
subsequent operations.

## Selectors

Selectors provide methods to extract all or a subset of a feature type in the referenced
object. These methods select Edges, Faces, Solids, Vertices, or Wires in Builder objects
or from Shape objects themselves. All of these methods return a [`ShapeList`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList "topology.ShapeList"),
which is a subclass of `list` and may be sorted, grouped, or filtered by
[Operators](https://build123d.readthedocs.io/en/latest/topology_selection.html#operators).

### Overview

| Selector | Criteria | Applicability | Description |
| --- | --- | --- | --- |
| [`vertices()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.vertices "topology.Shape.vertices") | ALL, LAST | `BuildLine`, `BuildSketch`, `BuildPart` | `Vertex` extraction |
| [`edges()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.edges "topology.Shape.edges") | ALL, LAST, NEW | `BuildLine`, `BuildSketch`, `BuildPart` | `Edge` extraction |
| [`wires()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.wires "topology.Shape.wires") | ALL, LAST | `BuildLine`, `BuildSketch`, `BuildPart` | `Wire` extraction |
| [`faces()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.faces "topology.Shape.faces") | ALL, LAST | `BuildSketch`, `BuildPart` | `Face` extraction |
| [`solids()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.solids "topology.Shape.solids") | ALL, LAST | `BuildPart` | `Solid` extraction |

Both shape objects and builder objects have access to selector methods to select all of
a feature as long as they can contain the feature being selected.

```python
```build123d
# In context
with BuildSketch() as context:
    Rectangle(1, 1)
    context.edges()

    # Build context implicitly has access to the selector
    edges()

# Taking the sketch out of context
context.sketch.edges()

# Create sketch out of context
Rectangle(1, 1).edges()
```

### Select In Build Context

Build contexts track the last operation and their selector methods can take
[`Select`](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select") as criteria to specify a subset of
features to extract. By default, a selector will select `ALL` of a feature, while
`LAST` selects features created or altered by the most recent operation. [`edges()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.edges "topology.Shape.edges") can
uniquely specify `NEW` to only select edges created in the last operation which neither
existed in the referenced object before the last operation, nor the modifying object.

Important

[`Select`](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.Select "build_enums.Select") as selector criteria is only valid for builder objects!

```python
```build123d
# In context
with BuildPart() as context:
    Box(2, 2, 1)
    Cylinder(1, 2)
    context.edges(Select.LAST)

# Does not work out of context!
context.part.edges(Select.LAST)
(Box(2, 2, 1) + Cylinder(1, 2)).edges(Select.LAST)
```

Create a simple part to demonstrate selectors. Select using the default criteria
`Select.ALL`. Specifying `Select.ALL` for the selector is not required.

```python
```build123d
with BuildPart() as part:
    Box(5, 5, 1)
    Cylinder(1, 5)

    part.vertices()
    part.edges()
    part.faces()

    # Is the same as
    part.vertices(Select.ALL)
    part.edges(Select.ALL)
    part.faces(Select.ALL)
```

![_images/selectors_select_all.png](https://build123d.readthedocs.io/en/latest/_images/selectors_select_all.png)

The default `Select.ALL` features

Select features changed in the last operation with criteria `Select.LAST`.

```python
```build123d
with BuildPart() as part:
    Box(5, 5, 1)
    Cylinder(1, 5)

    part.vertices(Select.LAST)
    part.edges(Select.LAST)
    part.faces(Select.LAST)
```

![_images/selectors_select_last.png](https://build123d.readthedocs.io/en/latest/_images/selectors_select_last.png)

`Select.LAST` features

Select only new edges from the last operation with `Select.NEW`. This option is only
available for a `ShapeList` of edges!

```python
```build123d
with BuildPart() as part:
    Box(5, 5, 1)
    Cylinder(1, 5)

    part.edges(Select.NEW)
```

![_images/selectors_select_new.png](https://build123d.readthedocs.io/en/latest/_images/selectors_select_new.png)

`Select.NEW` edges where box and cylinder intersect

This only returns new edges which are not reused from Box or Cylinder, in this case where
the objects intersect. But what happens if the objects don’t intersect and all the
edges are reused?

```python
```build123d
with BuildPart() as part:
    Box(5, 5, 1, align=(Align.CENTER, Align.CENTER, Align.MAX))
    Cylinder(2, 2, align=(Align.CENTER, Align.CENTER, Align.MIN))

    part.edges(Select.NEW)
```

![_images/selectors_select_new_none.png](https://build123d.readthedocs.io/en/latest/_images/selectors_select_new_none.png)

`Select.NEW` edges when box and cylinder don’t intersect

No edges are selected! Unlike the previous example, the Edge between the Box and Cylinder
objects is an edge reused from the Cylinder. Think of `Select.NEW` as a way to select
only completely new edges created by the operation.

Note

Chamfer and fillet modify the current object, but do not have new edges via
`Select.NEW`.

```python
```build123d
with BuildPart() as part:
    Box(5, 5, 1)
    Cylinder(1, 5)
    edges = part.edges().filter_by(lambda a: a.length == 1)
    fillet(edges, 1)

    part.edges(Select.NEW)
```

![_images/selectors_select_new_fillet.png](https://build123d.readthedocs.io/en/latest/_images/selectors_select_new_fillet.png)

Left, `Select.NEW` returns no edges after fillet. Right, `Select.LAST`

### Select New Edges In Algebra Mode

The utility method `new_edges` compares one or more shape objects to a
another “combined” shape object and returns the edges new to the combined shape.
`new_edges` is available both Algebra mode or Builder mode, but is necessary in
Algebra Mode where `Select.NEW` is unavailable

```python
```build123d
box = Box(5, 5, 1)
circle = Cylinder(2, 5)
part = box + circle
edges = new_edges(box, circle, combined=part)
```

![_images/selectors_new_edges.png](https://build123d.readthedocs.io/en/latest/_images/selectors_new_edges.png)

`new_edges` can also find edges created during a chamfer or fillet operation by
comparing the object before the operation to the “combined” object.

```python
```build123d
box = Box(5, 5, 1)
circle = Cylinder(2, 5)
part_before = box + circle
edges = part_before.edges().filter_by(lambda a: a.length == 1)
part = fillet(edges, 1)
edges = new_edges(part_before, combined=part)
```

![_images/operators_group_area.png](https://build123d.readthedocs.io/en/latest/_images/operators_group_area.png)

## Operators

Operators provide methods refine a `ShapeList` of features isolated by a *selector* to
further specify feature(s). These methods can sort, group, or filter `ShapeList`
objects and return a modified `ShapeList`, or in the case of [`group_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.group_by "topology.ShapeList.group_by"), `GroupBy`,
a list of `ShapeList` objects accessible by index or key.

### Overview

| Method | Criteria | Description |
| --- | --- | --- |
| [`sort_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.sort_by "topology.ShapeList.sort_by") | `Axis`, `Edge`, `Wire`, `SortBy`, callable, property | Sort `ShapeList` by criteria |
| [`sort_by_distance()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.sort_by_distance "topology.ShapeList.sort_by_distance") | `Shape`, `VectorLike` | Sort `ShapeList` by distance from criteria |
| [`group_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.group_by "topology.ShapeList.group_by") | `Axis`, `Edge`, `Wire`, `SortBy`, callable, property | Group `ShapeList` by criteria |
| [`filter_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.filter_by "topology.ShapeList.filter_by") | `Axis`, `Plane`, `GeomType`, `ShapePredicate`, property | Filter `ShapeList` by criteria |
| [`filter_by_position()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.filter_by_position "topology.ShapeList.filter_by_position") | `Axis` | Filter `ShapeList` by `Axis` & mix / max values |

Operator methods take criteria to refine `ShapeList`. Broadly speaking, the criteria
fall into the following categories, though not all operators take all criteria:

- Geometric objects: `Axis`, `Plane`
- Topological objects: `Edge`, `Wire`
- Enums: [`SortBy`](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.SortBy "build_enums.SortBy"), [`GeomType`](https://build123d.readthedocs.io/en/latest/builder_api_reference.html#build_enums.GeomType "build_enums.GeomType")
- Properties, eg: `Face.area`, `Edge.length`
- `ShapePredicate`, eg: `lambda e: e.is_interior == 1`, `lambda f: lf.edges() >= 3`
- Callable eg: `Vertex().distance`

### Sort

A `ShapeList` can be sorted with the [`sort_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.sort_by "topology.ShapeList.sort_by") and [`sort_by_distance()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.sort_by_distance "topology.ShapeList.sort_by_distance")
methods based on a sorting criteria. Sorting is a critical step when isolating individual
features as a `ShapeList` from a selector is typically unordered.

Here we want to capture some vertices from the object furthest along `X`: All the
vertices are first captured with the [`vertices()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.vertices "topology.Shape.vertices") selector, then sort by `Axis.X`.
Finally, the vertices can be captured with a list slice for the last 4 list items, as the
items are sorted from least to greatest `X` position. Remember, `ShapeList` is a
subclass of `list`, so any list slice can be used.

```python
```build123d
part.vertices().sort_by(Axis.X)[-4:]
```

![_images/operators_sort_x.png](https://build123d.readthedocs.io/en/latest/_images/operators_sort_x.png)

#### Examples

![](https://build123d.readthedocs.io/en/latest/_images/thumb_sort_sortby.png)

SortBy

[SortBy](https://build123d.readthedocs.io/en/latest/topology_selection/sort_examples.html#sort-sortby)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_sort_along_wire.png)

Along Wire

[Along Wire](https://build123d.readthedocs.io/en/latest/topology_selection/sort_examples.html#sort-along-wire)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_sort_axis.png)

Axis

[Axis](https://build123d.readthedocs.io/en/latest/topology_selection/sort_examples.html#sort-axis)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_sort_distance.png)

Distance From

[Distance From](https://build123d.readthedocs.io/en/latest/topology_selection/sort_examples.html#sort-distance-from)

### Group

A ShapeList can be grouped and sorted with the [`group_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.group_by "topology.ShapeList.group_by") method based on a grouping
criteria. Grouping can be a great way to organize features without knowing the values of
specific feature properties. Rather than returning a `ShapeList`, [`group_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.group_by "topology.ShapeList.group_by") returns
a `GroupBy`, a list of `ShapeList` objects sorted by the grouping criteria.
`GroupBy` can be printed to view the members of each group, indexed like a list to
retrieve a `ShapeList`, and be accessed using a key with the `group` method. If the
group keys are unknown they can be discovered with `key_to_group_index`.

If we want only the edges from the smallest faces by area we can get the faces, then
group by `SortBy.AREA`. The `ShapeList` of smallest faces is available from the first
list index. Finally, a `ShapeList` has access to selectors, so calling [`edges()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.Shape.edges "topology.Shape.edges") will
return a new list of all edges in the previous list.

```python
```build123d
part.faces().group_by(SortBy.AREA)[0].edges())
```

![_images/operators_group_area.png](https://build123d.readthedocs.io/en/latest/_images/operators_group_area.png)

#### Examples

![](https://build123d.readthedocs.io/en/latest/_images/thumb_group_axis.png)

Axis and Length

[Axis and Length](https://build123d.readthedocs.io/en/latest/topology_selection/group_examples.html#group-axis)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_group_hole_area.png)

Hole Area

[Hole Area](https://build123d.readthedocs.io/en/latest/topology_selection/group_examples.html#group-hole-area)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_group_properties_with_keys.png)

Properties with Keys

[Properties with Keys](https://build123d.readthedocs.io/en/latest/topology_selection/group_examples.html#group-properties-with-keys)

### Filter

A `ShapeList` can be filtered with the [`filter_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.filter_by "topology.ShapeList.filter_by") and [`filter_by_position()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.filter_by_position "topology.ShapeList.filter_by_position") methods based
on a filtering criteria. Filters are flexible way to isolate (or exclude) features based
on known criteria.

Lets say we need all the faces with a normal in the `+Z` direction. One way to do this
might be with a list comprehension, however [`filter_by()`](https://build123d.readthedocs.io/en/latest/direct_api_reference.html#topology.ShapeList.filter_by "topology.ShapeList.filter_by") has the capability to take a
lambda function as a filter condition on the entire list. In this case, the normal of
each face can be checked against a vector direction and filtered accordingly.

```python
```build123d
part.faces().filter_by(lambda f: f.normal_at() == Vector(0, 0, 1))
```

![_images/operators_filter_z_normal.png](https://build123d.readthedocs.io/en/latest/_images/operators_filter_z_normal.png)

#### Examples

![](https://build123d.readthedocs.io/en/latest/_images/thumb_filter_geomtype.png)

GeomType

[GeomType](https://build123d.readthedocs.io/en/latest/topology_selection/filter_examples.html#filter-geomtype)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_filter_all_edges_circle.png)

All Edges Circle

[All Edges Circle](https://build123d.readthedocs.io/en/latest/topology_selection/filter_examples.html#filter-all-edges-circle)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_filter_axisplane.png)

Axis and Plane

[Axis and Plane](https://build123d.readthedocs.io/en/latest/topology_selection/filter_examples.html#filter-axis-plane)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_filter_inner_wire_count.png)

Inner Wire Count

[Inner Wire Count](https://build123d.readthedocs.io/en/latest/topology_selection/filter_examples.html#filter-inner-wire-count)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_filter_nested.png)

Nested Filters

[Nested Filters](https://build123d.readthedocs.io/en/latest/topology_selection/filter_examples.html#filter-nested)

![](https://build123d.readthedocs.io/en/latest/_images/thumb_filter_shape_properties.png)

Shape Properties

[Shape Properties](https://build123d.readthedocs.io/en/latest/topology_selection/filter_examples.html#filter-shape-properties)
