from __future__ import annotations

from pydantic import BaseModel, Field

from formloop.models import NormalizedSpec, ReviewSummary


class ManagerAssessment(BaseModel):
    normalized_spec: NormalizedSpec
    needs_clarification: bool = False
    clarification_reason: str | None = None
    clarification_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    research_topics: list[str] = Field(default_factory=list)


class ResearchOutput(BaseModel):
    topic: str
    findings: list[str]
    citations: list[str] = Field(default_factory=list)


class DesignerOutput(BaseModel):
    model_source: str
    rationale: str
    expected_features: list[str] = Field(default_factory=list)


class ReviewPlan(BaseModel):
    requested_measurements: list[str] = Field(default_factory=list)
    requested_feature_checks: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReviewOutput(BaseModel):
    summary: ReviewSummary


class EvalJudgePlan(BaseModel):
    requested_measurements: list[str] = Field(default_factory=list)
    requested_comparisons: list[str] = Field(default_factory=list)


class EvalJudgeOutput(BaseModel):
    spec_adherence_score: float
    dimensional_compliance_score: float
    notes: list[str] = Field(default_factory=list)
    acceptable: bool = False

