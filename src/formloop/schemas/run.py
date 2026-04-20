"""Run contract.

REQ: FLH-F-001, FLH-F-011, FLH-F-021, FLH-F-023, FLH-D-006, FLH-D-013
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from ._common import SchemaModel, utcnow_iso


class RunStatus(str, Enum):
    created = "created"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class AssumptionRecord(SchemaModel):
    """A manager-recorded assumption made when spec is ambiguous (FLH-F-020)."""

    topic: str
    assumption: str
    recorded_at: str = Field(default_factory=utcnow_iso)


class EffectiveRuntime(SchemaModel):
    """Effective runtime metadata used for this run (FLH-D-017)."""

    profile: str
    model: str
    reasoning: str


class AgentAnswer(SchemaModel):
    """Final user-facing answer synthesized by the manager (FLH-F-002)."""

    text: str
    delivered_revision_name: str | None = None


class Run(SchemaModel):
    """Top-level persisted design or eval thread.

    Revisions exist only after a candidate artifact bundle has been
    generated and persisted (FLH-F-022).
    """

    run_id: str = Field(description="Opaque unique id (uuid4).")
    run_name: str = Field(description="Human-readable sequential name like run-0001.")
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)

    input_summary: str
    reference_image: str | None = None

    current_spec: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[AssumptionRecord] = Field(default_factory=list)

    revisions: list[str] = Field(
        default_factory=list, description="Ordered list of revision names (rev-001, ...)."
    )
    current_revision_id: str | None = None

    effective_runtime: EffectiveRuntime

    status: RunStatus = RunStatus.created
    status_detail: str | None = None

    final_answer: AgentAnswer | None = None
