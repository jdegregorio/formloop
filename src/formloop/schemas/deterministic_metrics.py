"""Persisted deterministic eval metrics output.

REQ: FLH-F-014, FLH-F-015, FLH-V-008
"""

from __future__ import annotations

from pydantic import Field

from ._common import SchemaModel


class DeterministicMetrics(SchemaModel):
    """Deterministic metrics for a single eval case (wraps cad compare)."""

    case_id: str
    mode: str = Field(description="'exact' or 'mesh_fallback' (from cad compare).")
    alignment: str
    left_volume: float | None = None
    right_volume: float | None = None
    shared_volume: float | None = None
    left_only_volume: float | None = None
    right_only_volume: float | None = None
    union_volume: float | None = None
    overlap_ratio: float | None = None
    bbox_match: bool | None = None
    hole_count_match: bool | None = None
    notes: list[str] = Field(default_factory=list)
