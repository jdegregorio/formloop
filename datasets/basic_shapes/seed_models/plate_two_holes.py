"""Seed model — 40x24x8 plate with two 6mm through-holes 20mm apart."""

from __future__ import annotations

from build123d import Box, Cylinder, Pos


def build_model(params: dict, context: object):
    width = float(params.get("width", 40.0))
    depth = float(params.get("depth", 24.0))
    height = float(params.get("height", 8.0))
    diameter = float(params.get("hole_diameter", 6.0))
    centers = params.get("hole_centers", [[-10.0, 0.0], [10.0, 0.0]])
    shape = Box(width, depth, height)
    for x_value, y_value in centers:
        shape = shape - Pos(float(x_value), float(y_value), 0.0) * Cylinder(diameter / 2.0, height)
    return shape
