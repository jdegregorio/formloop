"""Post-mortem specialist — analyzes a completed run for harness optimization.

REQ: FLH-NF-007, FLH-V-003

Reviews logs, events, CAD validation attempts, review summaries, and final
status from one completed run, and emits GitHub-issue-style development
requests aimed at improving harness quality, latency, reliability, cost, or
observability. The orchestrator owns context collection and persistence; this
module owns the agent definition and structured output contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from .common import Agent, build_model_settings, lenient_output


class PostMortemIssue(BaseModel):
    title: str = Field(description="Short GitHub-issue-style title.")
    category: str = Field(
        description="One of: latency, quality, reliability, observability, cost, product."
    )
    severity: str = Field(description="One of: low, medium, high, critical.")
    evidence: list[str] = Field(default_factory=list)
    impact: str
    suggested_fix: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)


class RunPostMortem(BaseModel):
    run_name: str
    summary: str
    key_issues: list[PostMortemIssue] = Field(default_factory=list)


INSTRUCTIONS = """You are a Formloop harness post-mortem analyst.

Review one completed run's logs, events, CAD validation attempts, review
summaries, and final status. Produce GitHub-issue-style development requests
for root causes that hurt quality, latency, reliability, cost, or observability.

Rules:
- Be specific and evidence-backed. Cite timings, failed commands, review
  decisions, missing artifacts, and repeated failure patterns when present.
- Prefer 2-6 high-signal issues, not a laundry list.
- Distinguish root causes from symptoms.
- If a deterministic gate could have avoided an LLM review, call that out.
- Do not include secrets. Do not ask for paid external services.
- Keep issue bodies actionable enough to drive future development."""


def build_postmortem_agent(profile: Profile) -> Agent[None]:
    return Agent(
        name="postmortem",
        instructions=INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        output_type=lenient_output(RunPostMortem),
    )


__all__ = [
    "PostMortemIssue",
    "RunPostMortem",
    "build_postmortem_agent",
]
