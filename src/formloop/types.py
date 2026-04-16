from __future__ import annotations

from enum import Enum


class ThinkingLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProviderKind(str, Enum):
    OPENAI_RESPONSES = "openai_responses"
    LITELLM = "litellm"


class RunMode(str, Enum):
    DESIGN = "design"
    EVAL = "eval"


class RunStatus(str, Enum):
    PENDING = "pending"
    NEEDS_CLARIFICATION = "needs_clarification"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ReviewDecision(str, Enum):
    PASS = "pass"
    REVISE = "revise"


class ArtifactKind(str, Enum):
    STEP = "step"
    GLB = "glb"
    RENDER_SHEET = "render_sheet"
    MODEL_SOURCE = "model_source"
    REVIEW_SUMMARY = "review_summary"
    METRICS = "metrics"
    JUDGE_OUTPUT = "judge_output"
    REFERENCE_IMAGE = "reference_image"
    AUXILIARY = "auxiliary"


class TraceKind(str, Enum):
    PROGRESS = "progress"
    TOOL_CALL = "tool_call"
    SUBAGENT_CALL = "subagent_call"
    CLARIFICATION = "clarification"
    ASSUMPTION = "assumption"
    REVIEW = "review"
    RESEARCH = "research"
    ERROR = "error"

