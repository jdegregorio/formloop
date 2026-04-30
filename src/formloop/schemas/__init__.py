"""Pydantic mirrors of the checked-in JSON schemas.

REQ: FLH-D-021, FLH-D-022  — stable machine-readable contracts versioned in-repo.

Every model here emits JSON Schema via ``model.model_json_schema()`` and the
checked-in ``schemas/*.schema.json`` files are expected to match byte-for-byte
(generated via ``scripts/sync_schemas.py``).
"""

from .artifact_manifest import ArtifactEntry, ArtifactManifest
from .deterministic_metrics import DeterministicMetrics
from .judge_output import JudgeOutput
from .progress_event import ProgressEvent, ProgressEventKind
from .reference_upload import ReferenceImageUploadResponse
from .review_summary import ReviewDecision, ReviewOutcome, ReviewSummary
from .revision import Revision, RevisionTrigger
from .run import (
    AgentAnswer,
    AssumptionRecord,
    EffectiveRuntime,
    RoleRuntime,
    Run,
    RunStatus,
)
from .run_create import RunCreateRequest, RunCreateResponse
from .run_snapshot import RunSnapshot, SnapshotArtifacts

__all__ = [
    "AgentAnswer",
    "ArtifactEntry",
    "ArtifactManifest",
    "AssumptionRecord",
    "DeterministicMetrics",
    "EffectiveRuntime",
    "JudgeOutput",
    "ProgressEvent",
    "ProgressEventKind",
    "ReferenceImageUploadResponse",
    "ReviewDecision",
    "ReviewOutcome",
    "ReviewSummary",
    "Revision",
    "RevisionTrigger",
    "RoleRuntime",
    "Run",
    "RunCreateRequest",
    "RunCreateResponse",
    "RunSnapshot",
    "RunStatus",
    "SnapshotArtifacts",
]

SCHEMA_VERSION = 1
