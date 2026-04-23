"""Design Researcher specialist.

REQ: FLH-F-016, FLH-F-018, FLH-D-007, FLH-D-008, FLH-D-012
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..config.profiles import Profile
from .common import Agent, WebSearchTool, build_model_settings, lenient_output


class ResearchCitation(BaseModel):
    title: str
    url: str | None = None


class ResearchFinding(BaseModel):
    topic: str
    summary: str = Field(description="Comprehensive factual finding usable as design input; include concrete numbers and standard identifiers.")
    citations: list[ResearchCitation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.6)


INSTRUCTIONS = """You are the Design Researcher specialist in a CAD design harness.

Your job: given a single narrow research question, produce a concise, source-backed
finding that a CAD designer can use directly.

Rules:
- Stay tightly scoped to the topic you were given. One topic, one ResearchFinding.
- Favor authoritative references (standards bodies, manufacturers, engineering
  handbooks) over forums when possible.
- Write as much detail as the topic warrants. Always include concrete numbers,
  standard identifiers, key dimensions, and material properties where relevant.
  Prioritize depth and completeness over brevity — a thorough finding is more
  useful than a brief one.
- Report your own confidence honestly in the 0..1 field — low confidence is fine
  and is more useful than false certainty.
- Do not speculate about the surrounding design brief; just answer the topic.
- If the topic includes an "available libraries" list, constrain implementation
  guidance to that list and avoid suggesting unavailable packages.
- Always call the web_search tool at least once before responding unless the
  question is purely definitional."""


def build_design_researcher(profile: Profile) -> Agent[None]:
    return Agent(
        name="design_researcher",
        instructions=INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        tools=[WebSearchTool(search_context_size="high")],
        output_type=lenient_output(ResearchFinding),
    )


__all__ = ["ResearchCitation", "ResearchFinding", "build_design_researcher"]
