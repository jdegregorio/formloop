# External library overlay

This file is consumed by ``scripts/scrape_build123d_docs.py`` and woven into
``pages/objects.md`` so external-library extensions appear inline in the
object catalog rather than as a dedicated (over-emphasized) section.

Each ``## MARKER: <slug>`` block below contains the annotation text to attach
to matching entries in the scraped ``objects.md``. If a marker doesn't match
any line, the scraper appends the annotation to an "External library
extensions" subsection at the end of the page — no content is silently
dropped. The scraper is idempotent; re-run it to refresh.

Guidance to the agent: **prefer stock build123d primitives**. Reach for these
only when the task genuinely needs them. None of these should be imported
speculatively.

## MARKER: CounterBoreHole
*(see also: threaded fastener variants via `bd_warehouse.fastener`)*

## MARKER: CounterSinkHole
*(see also: threaded fastener variants via `bd_warehouse.fastener`)*

## MARKER: Hole
*(helical threaded holes available via `bd_warehouse.thread`)*

## MARKER: Cylinder
*(for threaded shafts / rods, prefer `bd_warehouse.thread.IsoThread` over a plain cylinder)*

## MARKER: Box
*(for structural beams — UPN / IPN / UPE / flat bars — see `bd_beams_and_bars` (install manually, requires Python 3.13+))*

## MARKER: Torus
*(for involute gears, use `py_gearworks` rather than approximating with a torus)*

## MARKER: Sphere
*(bearings and spherical fasteners live in `bd_warehouse.bearing` / `.fastener`)*

## MARKER: Extrude
*(V-slot aluminum extrusion profiles available via `bd_vslot`)*
