"""HTTP request/response contracts for creating a run.

REQ: FLH-F-025, FLH-D-019, FLH-D-022
"""

from __future__ import annotations

from pydantic import Field, field_validator

from ..config.profiles import validate_reasoning, validate_runtime_role
from ._common import SchemaModel


class RunCreateRequest(SchemaModel):
    """Minimum payload to start a run."""

    prompt: str = Field(min_length=1)
    profile: str = Field(default="normal", description="One of the named profiles.")
    model: str | None = Field(default=None, description="Optional global model override.")
    effort: str | None = Field(default=None, description="Optional global reasoning override.")
    reference_image: str | None = Field(
        default=None,
        description="Optional path (server-side) to a reference image.",
    )
    max_revisions: int | None = Field(
        default=None, ge=1, description="Override the config default."
    )
    role_models: dict[str, str] = Field(
        default_factory=dict,
        description="Optional per-role model overrides, keyed by runtime role.",
    )
    role_reasoning: dict[str, str] = Field(
        default_factory=dict,
        description="Optional per-role reasoning overrides, keyed by runtime role.",
    )

    @field_validator("role_models")
    @classmethod
    def _validate_role_models(cls, value: dict[str, str]) -> dict[str, str]:
        return {validate_runtime_role(role): model for role, model in value.items()}

    @field_validator("role_reasoning")
    @classmethod
    def _validate_role_reasoning(cls, value: dict[str, str]) -> dict[str, str]:
        return {
            validate_runtime_role(role): validate_reasoning(
                reasoning, label=f"role {role!r} reasoning"
            )
            for role, reasoning in value.items()
        }

    @field_validator("effort")
    @classmethod
    def _validate_effort(cls, value: str | None) -> str | None:
        return validate_reasoning(value, label="effort") if value is not None else None


class RunCreateResponse(SchemaModel):
    """Minimum payload returned when a run is created."""

    run_id: str
    run_name: str
    status_url: str
    events_url: str
