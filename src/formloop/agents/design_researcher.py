"""Design Researcher agent definition."""

from __future__ import annotations

from agents import Agent, WebSearchTool

from ..models import ResearchFinding
from .common import HarnessAgentContext, reasoning_settings


def build_design_researcher_agent(*, model: str, reasoning: str) -> Agent[HarnessAgentContext]:
    # Req: FLH-F-003, FLH-F-016, FLH-D-007, FLH-D-008
    instructions = """
You are the Design Researcher for Formloop.

Use web search when factual research is required. Focus on standards, common dimensions,
part conventions, and naming. Return concise findings with source URLs only when they are
useful for the current CAD task.
"""
    return Agent[HarnessAgentContext](
        name="Design Researcher",
        handoff_description="Looks up standards, conventions, and factual design context.",
        instructions=instructions,
        model=model,
        model_settings=reasoning_settings(reasoning),
        output_type=ResearchFinding,
        tools=[WebSearchTool()],
    )
