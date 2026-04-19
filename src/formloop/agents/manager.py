"""Manager agent definitions."""

from __future__ import annotations

from agents import Agent

from ..models import ManagerNormalizationOutput
from .common import HarnessAgentContext, reasoning_settings


def build_manager_normalizer_agent(*, model: str, reasoning: str) -> Agent[HarnessAgentContext]:
    # Req: FLH-F-001, FLH-F-002, FLH-F-020, FLH-D-006
    instructions = """
You are the Formloop Manager.

Your job is to normalize the user's request into the current fit/form/function spec.
Be proactive. Infer likely assumptions when the direction is reasonably clear instead of
stalling for clarification. Record those assumptions explicitly.

Return:
- input_summary
- current_spec
- assumptions
- research_topics only when external factual research is genuinely needed
- initial_execution_plan as a short sequence of next actions
"""
    return Agent[HarnessAgentContext](
        name="Manager Normalizer",
        instructions=instructions,
        model=model,
        model_settings=reasoning_settings(reasoning),
        output_type=ManagerNormalizationOutput,
    )


def build_manager_delivery_agent(*, model: str, reasoning: str) -> Agent[HarnessAgentContext]:
    # Req: FLH-F-002, FLH-F-024
    instructions = """
You are the Formloop Manager preparing the final user-facing answer.

Summarize the delivered revision, what assumptions were made, what was reviewed, and any
remaining caveats. Be concise and operator-friendly.
"""
    return Agent[HarnessAgentContext](
        name="Manager Delivery",
        instructions=instructions,
        model=model,
        model_settings=reasoning_settings(reasoning),
    )
