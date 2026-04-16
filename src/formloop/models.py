from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from formloop.types import ArtifactKind, ReviewDecision, RunMode, RunStatus, TraceKind


def utc_now() -> datetime:
    return datetime.now(UTC)


class ReferenceImage(BaseModel):
    path: str
    label: str = "reference"


class DesignRequest(BaseModel):
    prompt: str
    profile: str | None = None
    reference_image: ReferenceImage | None = None
    requested_by: str = "operator"
    run_mode: RunMode = RunMode.DESIGN


class NormalizedSpec(BaseModel):
    summary: str
    fit: list[str] = Field(default_factory=list)
    form: list[str] = Field(default_factory=list)
    function: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    blocking_gaps: list[str] = Field(default_factory=list)
    key_dimensions: list[str] = Field(default_factory=list)


class ClarificationEvent(BaseModel):
    reason: str
    questions: list[str]
    blocking: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class AssumptionRecord(BaseModel):
    text: str
    rationale: str
    created_at: datetime = Field(default_factory=utc_now)


class ResearchFinding(BaseModel):
    topic: str
    findings: list[str]
    source_type: str = "builtin"
    citations: list[str] = Field(default_factory=list)


class ArtifactRecord(BaseModel):
    kind: ArtifactKind
    path: str
    revision: int
    label: str


class ToolCallRecord(BaseModel):
    tool: str
    command: list[str]
    cwd: str
    returncode: int
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class SubagentCallRecord(BaseModel):
    agent_name: str
    purpose: str
    prompt_excerpt: str
    created_at: datetime = Field(default_factory=utc_now)


class TraceEvent(BaseModel):
    kind: TraceKind
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ReviewSummary(BaseModel):
    decision: ReviewDecision
    confidence: float
    key_findings: list[str]
    missing_or_suspect_features: list[str] = Field(default_factory=list)
    suspect_dimensions: list[str] = Field(default_factory=list)
    reference_image_notes: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)


class RevisionRecord(BaseModel):
    revision_index: int
    model_source: str
    spec: NormalizedSpec
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    review_summary: ReviewSummary | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    subagent_calls: list[SubagentCallRecord] = Field(default_factory=list)
    research: list[ResearchFinding] = Field(default_factory=list)
    trace_events: list[TraceEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class EffectiveRuntime(BaseModel):
    profile: str
    provider: str
    model: str
    thinking: str
    backend: str


class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    status: RunStatus = RunStatus.PENDING
    mode: RunMode = RunMode.DESIGN
    prompt: str
    reference_image: ReferenceImage | None = None
    current_spec: NormalizedSpec | None = None
    clarifications: list[ClarificationEvent] = Field(default_factory=list)
    assumptions: list[AssumptionRecord] = Field(default_factory=list)
    revisions: list[RevisionRecord] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    subagent_calls: list[SubagentCallRecord] = Field(default_factory=list)
    trace_events: list[TraceEvent] = Field(default_factory=list)
    effective_runtime: EffectiveRuntime
    latest_review_summary: ReviewSummary | None = None
    final_artifacts: list[ArtifactRecord] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()


class EvalCase(BaseModel):
    case_id: str
    prompt: str
    normalized_spec: NormalizedSpec
    ground_truth_step: str
    reference_image: str | None = None
    tolerances: dict[str, float] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class EvalCaseResult(BaseModel):
    case_id: str
    run_id: str
    deterministic_metrics: dict[str, Any]
    judge_outputs: dict[str, Any]
    score_status: str
    summary_markdown: str
    artifact_bundle: list[ArtifactRecord]


class EvalBatchResult(BaseModel):
    dataset: str
    started_at: datetime = Field(default_factory=utc_now)
    case_results: list[EvalCaseResult]
    aggregate_metrics: dict[str, Any]
    failure_shortlist: list[str]
    report_path: str


def artifact_path(record: ArtifactRecord, root: Path) -> Path:
    return root / record.path
