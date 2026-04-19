"""Core runtime, persistence, and API contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .jsonutil import utc_now


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ReviewDecision(str, Enum):
    accept = "accept"
    revise = "revise"


class RunStatus(str, Enum):
    created = "created"
    running = "running"
    awaiting_review = "awaiting_review"
    completed = "completed"
    failed = "failed"


class EvalPassStatus(str, Enum):
    pass_ = "pass"
    fail = "fail"
    warning = "warning"


class ResearchTopic(StrictModel):
    topic_id: str
    question: str
    reason: str


class Citation(StrictModel):
    title: str
    url: str
    note: str | None = None


class ResearchFinding(StrictModel):
    topic_id: str
    summary: str
    citations: list[Citation] = Field(default_factory=list)


class NormalizedSpec(StrictModel):
    intent_summary: str
    fit_requirements: list[str] = Field(default_factory=list)
    form_requirements: list[str] = Field(default_factory=list)
    function_requirements: list[str] = Field(default_factory=list)
    dimensions_constraints: list[str] = Field(default_factory=list)
    required_features: list[str] = Field(default_factory=list)
    optional_reference_image: str | None = None
    open_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ManagerNormalizationOutput(StrictModel):
    input_summary: str
    current_spec: NormalizedSpec
    assumptions: list[str] = Field(default_factory=list)
    research_topics: list[ResearchTopic] = Field(default_factory=list)
    initial_execution_plan: list[str] = Field(default_factory=list)


class CadDesignOutput(StrictModel):
    model_name: str
    strategy: str
    source_code: str
    notes: list[str] = Field(default_factory=list)


class ReviewSummary(StrictModel):
    decision: ReviewDecision
    confidence: float = Field(ge=0.0, le=1.0)
    key_findings: list[str] = Field(default_factory=list)
    suspect_or_missing_features: list[str] = Field(default_factory=list)
    suspect_dimensions_to_recheck: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)
    summary: str


class JudgeOutput(StrictModel):
    mode: str
    score: float = Field(ge=0.0, le=1.0)
    pass_status: EvalPassStatus
    rationale: str
    issues: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class ArtifactEntry(StrictModel):
    role: str
    path: str
    format: str
    required: bool = True
    sha256: str | None = None
    size_bytes: int | None = None


class ArtifactManifest(StrictModel):
    schema_version: int = 1
    entries: dict[str, ArtifactEntry]


class RevisionRecord(StrictModel):
    revision_id: str
    revision_name: str
    ordinal: int
    created_at: datetime = Field(default_factory=utc_now)
    trigger: str
    status: str
    spec_snapshot: NormalizedSpec
    artifact_manifest_path: str
    review_summary_path: str | None = None
    workspace_path: str | None = None


class RunRecord(StrictModel):
    run_id: str
    run_name: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    prompt: str
    input_summary: str
    reference_image: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    revisions: list[RevisionRecord] = Field(default_factory=list)
    current_revision_id: str | None = None
    effective_profile: str
    effective_model: str
    effective_reasoning: str
    current_spec: NormalizedSpec
    current_status_summary: str
    artifact_references: dict[str, str] = Field(default_factory=dict)
    review_outputs: dict[str, str] = Field(default_factory=dict)
    progress_events: list[str] = Field(default_factory=list)
    research_findings: list[ResearchFinding] = Field(default_factory=list)
    status: RunStatus = RunStatus.created


class ArtifactSummaryItem(StrictModel):
    role: str
    path: str


class RunSnapshot(StrictModel):
    run_id: str
    run_name: str
    status: RunStatus
    current_spec_summary: str
    latest_revision_id: str | None = None
    latest_review_summary_path: str | None = None
    artifact_summary: list[ArtifactSummaryItem] = Field(default_factory=list)
    last_event_reference: str | None = None


class ProgressEvent(StrictModel):
    event_id: str
    created_at: datetime = Field(default_factory=utc_now)
    event_type: str
    status: str
    breadcrumb: str
    data: dict[str, Any] = Field(default_factory=dict)


class RunCreateRequest(StrictModel):
    prompt: str
    profile: str | None = None
    reference_image: str | None = None


class RunCreateResponse(StrictModel):
    run_id: str
    run_name: str
    status: RunStatus
    snapshot_path: str


class DeterministicMetricsOutput(StrictModel):
    case_id: str | None = None
    run_id: str | None = None
    revision_id: str | None = None
    compare_metrics: dict[str, Any] = Field(default_factory=dict)
    candidate_summary: dict[str, Any] = Field(default_factory=dict)
    ground_truth_summary: dict[str, Any] = Field(default_factory=dict)
    pass_thresholds: dict[str, Any] = Field(default_factory=dict)
    pass_status: EvalPassStatus = EvalPassStatus.warning


class EvalCase(StrictModel):
    case_id: str
    prompt: str
    normalized_spec: NormalizedSpec
    ground_truth_step: str
    reference_image: str | None = None
    tolerances: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class EvalCaseResult(StrictModel):
    case_id: str
    run_id: str
    revision_id: str | None
    metrics_path: str
    judge_output_path: str
    pass_status: EvalPassStatus
    summary: str


class EvalAggregateReport(StrictModel):
    report_id: str
    created_at: datetime = Field(default_factory=utc_now)
    dataset_path: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    warning_cases: int
    case_results: list[EvalCaseResult]


class DoctorCheck(StrictModel):
    name: str
    ok: bool
    detail: str


def schema_models() -> dict[str, type[BaseModel]]:
    # Req: FLH-D-021, FLH-D-022
    return {
        "artifact-manifest": ArtifactManifest,
        "deterministic-metrics-output": DeterministicMetricsOutput,
        "judge-output": JudgeOutput,
        "progress-event": ProgressEvent,
        "review-summary": ReviewSummary,
        "revision": RevisionRecord,
        "run": RunRecord,
        "run-create-request": RunCreateRequest,
        "run-create-response": RunCreateResponse,
        "run-snapshot": RunSnapshot,
    }
