"""HTTP request/response contracts for creating a run.

REQ: FLH-F-025, FLH-D-019, FLH-D-022
"""

from __future__ import annotations

from pydantic import Field

from ._common import SchemaModel


class RunCreateRequest(SchemaModel):
    """Minimum payload to start a run."""

    prompt: str = Field(min_length=1)
    profile: str = Field(default="normal", description="One of the named profiles.")
    reference_image: str | None = Field(
        default=None,
        description="Optional path (server-side) to a reference image.",
    )
    max_revisions: int | None = Field(
        default=None, ge=1, description="Override the config default."
    )


class RunCreateResponse(SchemaModel):
    """Minimum payload returned when a run is created."""

    run_id: str
    run_name: str
    status_url: str
    events_url: str
