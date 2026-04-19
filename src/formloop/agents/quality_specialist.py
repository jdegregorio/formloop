"""Quality Specialist agent definition."""

from __future__ import annotations

from agents import Agent

from ..models import JudgeOutput, ReviewSummary
from .common import HarnessAgentContext, reasoning_settings


def build_quality_specialist_agent(
    *,
    model: str,
    reasoning: str,
    mode: str,
) -> Agent[HarnessAgentContext]:
    # Req: FLH-F-003, FLH-F-006, FLH-F-007, FLH-F-015
    if mode == "dev_eval":
        output_type: type[JudgeOutput] | type[ReviewSummary] = JudgeOutput
        instructions = """
You are the Quality Specialist in developer-eval mode.

Judge the candidate using deterministic metrics first. Treat overlap, missing volume,
and geometry mismatches as primary evidence. Produce a grounded pass/fail style output
with concise rationale and actionable issues.
"""
    else:
        output_type = ReviewSummary
        instructions = """
You are the Quality Specialist in normal design-review mode.

Judge the latest candidate against:
- the normalized spec
- rendered outputs
- deterministic inspect summaries
- at most one optional reference image

Choose accept only when the candidate appears good enough to deliver as the current best
revision. Otherwise choose revise and provide concrete revision instructions.
"""

    return Agent[HarnessAgentContext](
        name=f"Quality Specialist ({mode})",
        handoff_description="Performs structured candidate review or eval judging.",
        instructions=instructions,
        model=model,
        model_settings=reasoning_settings(reasoning),
        output_type=output_type,
    )
