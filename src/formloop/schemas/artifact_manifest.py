"""Artifact manifest contract.

REQ: FLH-F-009, FLH-D-024
"""

from __future__ import annotations

from pydantic import Field

from ._common import SchemaModel


class ArtifactEntry(SchemaModel):
    """One artifact in a revision bundle, keyed by stable role."""

    role: str = Field(description="Stable role like 'step', 'glb', 'render_sheet', 'view_front'.")
    path: str = Field(description="Path relative to the revision folder.")
    format: str = Field(description="'step' | 'glb' | 'png' | 'json' | ...")
    required: bool = True
    sha256: str | None = None
    size_bytes: int | None = None


class ArtifactManifest(SchemaModel):
    """Stable listing of a revision's artifacts by role."""

    revision_name: str
    entries: list[ArtifactEntry]
