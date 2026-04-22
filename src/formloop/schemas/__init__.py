"""Pydantic mirrors of the checked-in JSON schemas.

REQ: FLH-D-021, FLH-D-022  — stable machine-readable contracts versioned in-repo.

Every model here emits JSON Schema via ``model.model_json_schema()`` and the
checked-in ``schemas/*.schema.json`` files are expected to match byte-for-byte
(generated via ``scripts/sync_schemas.py``).
"""

from .run import (
    AgentAnswer,
    AssumptionRecord,
    EffectiveRuntime,
    Run,
    RunStatus,
)
from .revision import Revision, RevisionTrigger
from .artifact_manifest import ArtifactEntry, ArtifactManifest
from .review_summary import (
    ChecklistCategory,
    ChecklistItem,
    ChecklistMethod,
    ChecklistVerdict,
    ReviewDecision,
    ReviewSummary,
)
from .run_snapshot import RunSnapshot, SnapshotArtifacts
from .progress_event import ProgressEvent, ProgressEventKind
from .deterministic_metrics import DeterministicMetrics
from .judge_output import JudgeOutput
from .run_create import RunCreateRequest, RunCreateResponse

__all__ = [
    "AgentAnswer",
    "ArtifactEntry",
    "ArtifactManifest",
    "AssumptionRecord",
    "ChecklistCategory",
    "ChecklistItem",
    "ChecklistMethod",
    "ChecklistVerdict",
    "DeterministicMetrics",
    "EffectiveRuntime",
    "JudgeOutput",
    "ProgressEvent",
    "ProgressEventKind",
    "ReviewDecision",
    "ReviewSummary",
    "Revision",
    "RevisionTrigger",
    "Run",
    "RunCreateRequest",
    "RunCreateResponse",
    "RunSnapshot",
    "RunStatus",
    "SnapshotArtifacts",
]

SCHEMA_VERSION = 1
