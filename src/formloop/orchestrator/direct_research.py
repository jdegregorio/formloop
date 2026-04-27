"""Direct OpenAI Responses research helper.

REQ: FLH-F-016, FLH-F-018
"""

from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from ..config.profiles import Profile


class ResearchCitation(BaseModel):
    title: str
    url: str | None = None


class ResearchFinding(BaseModel):
    topic: str
    summary: str = Field(
        description=(
            "Comprehensive factual finding usable as design input; include concrete "
            "numbers and standard identifiers."
        )
    )
    citations: list[ResearchCitation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.6)


INSTRUCTIONS = """You are performing direct research for a CAD design harness.

Given one narrow research topic, produce a concise, source-backed
ResearchFinding that a CAD designer can use directly.

Rules:
- Stay tightly scoped to the topic. One topic, one ResearchFinding.
- Use web search for factual grounding.
- Favor authoritative references such as standards bodies, manufacturers, and
  engineering handbooks.
- Include concrete numbers, standard identifiers, key dimensions, and material
  properties when relevant.
- Report confidence honestly in the 0..1 field.
- Keep the final summary under 500 words.
"""


def _citation_key(citation: ResearchCitation) -> tuple[str, str | None]:
    return (citation.title, citation.url)


def _value(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _source_citations(response: Any) -> list[ResearchCitation]:
    citations: list[ResearchCitation] = []
    for item in getattr(response, "output", []) or []:
        action = _value(item, "action") or {}
        for source in _value(action, "sources") or []:
            title = str(_value(source, "title") or _value(source, "url") or "source")
            url = _value(source, "url")
            citations.append(ResearchCitation(title=title, url=str(url) if url else None))
        for content in _value(item, "content") or []:
            for annotation in _value(content, "annotations") or []:
                if _value(annotation, "type") != "url_citation":
                    continue
                title = str(_value(annotation, "title") or _value(annotation, "url") or "source")
                url = _value(annotation, "url")
                citations.append(ResearchCitation(title=title, url=str(url) if url else None))
    deduped: list[ResearchCitation] = []
    seen: set[tuple[str, str | None]] = set()
    for citation in citations:
        key = _citation_key(citation)
        if key not in seen:
            deduped.append(citation)
            seen.add(key)
    return deduped


async def research_topic_direct(
    topic: str,
    profile: Profile,
    *,
    timeout: float | None,
    client: AsyncOpenAI | None = None,
) -> dict[str, Any]:
    """Research one topic with a single Responses API call and web search."""

    openai_client = client or AsyncOpenAI()
    result = await asyncio.wait_for(
        openai_client.responses.parse(
            model=profile.model,
            reasoning={"effort": profile.reasoning},
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            max_tool_calls=1,
            include=["web_search_call.action.sources"],
            instructions=INSTRUCTIONS,
            input=f"Topic: {topic}",
            text_format=ResearchFinding,
        ),
        timeout=timeout,
    )
    finding = result.output_parsed
    if not isinstance(finding, ResearchFinding):
        finding = ResearchFinding.model_validate(finding)
    sources = _source_citations(result)
    if sources:
        existing = {_citation_key(c) for c in finding.citations}
        finding.citations.extend([c for c in sources if _citation_key(c) not in existing])
    return finding.model_dump()
