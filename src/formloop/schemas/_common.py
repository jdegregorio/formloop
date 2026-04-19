"""Shared base classes for formloop schema models.

REQ: FLH-D-021, FLH-D-022
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1


class SchemaModel(BaseModel):
    """Base for all formloop persisted contracts.

    Every persisted contract carries ``schema_version`` so consumers can
    detect contract drift without guessing.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: int = Field(default=SCHEMA_VERSION, ge=1)


def utcnow_iso() -> str:
    """Return an ISO-8601 UTC timestamp with second precision."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
