from __future__ import annotations

from types import SimpleNamespace

import pytest

from formloop.config.profiles import Profile
from formloop.orchestrator.direct_research import (
    ResearchFinding,
    _source_citations,
    research_topic_direct,
)

pytestmark = pytest.mark.asyncio


class _FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    async def parse(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            output_parsed=ResearchFinding(
                topic="topic-123",
                summary="Use M3 clearance diameter.",
                citations=[],
                confidence=0.8,
            ),
            output=[
                SimpleNamespace(
                    type="web_search_call",
                    action=SimpleNamespace(
                        sources=[
                            SimpleNamespace(
                                title="ISO source", url="https://example.test/iso"
                            )
                        ]
                    ),
                )
            ],
        )


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponses()


async def test_direct_research_uses_one_web_search_call_and_structured_output() -> None:
    client = _FakeClient()
    profile = Profile(name="test", model="gpt-test", reasoning="low")

    finding = await research_topic_direct(
        "topic-123",
        profile,
        timeout=5,
        client=client,  # type: ignore[arg-type]
    )

    assert client.responses.kwargs["model"] == "gpt-test"
    assert client.responses.kwargs["reasoning"] == {"effort": "low"}
    assert client.responses.kwargs["tools"] == [{"type": "web_search"}]
    assert client.responses.kwargs["max_tool_calls"] == 1
    assert client.responses.kwargs["text_format"] is ResearchFinding
    assert client.responses.kwargs["include"] == ["web_search_call.action.sources"]
    assert finding["topic"] == "topic-123"
    assert finding["citations"] == [
        {"title": "ISO source", "url": "https://example.test/iso"}
    ]


async def test_source_citations_do_not_serialize_parsed_response_items() -> None:
    def fail_model_dump(**kwargs):  # noqa: ARG001
        raise AssertionError("model_dump should not be called")

    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                model_dump=fail_model_dump,
                action=SimpleNamespace(
                    sources=[
                        SimpleNamespace(title="source attr", url="https://example.test/a")
                    ]
                ),
                content=[
                    SimpleNamespace(
                        annotations=[
                            SimpleNamespace(
                                type="url_citation",
                                title="annotation attr",
                                url="https://example.test/b",
                            )
                        ]
                    )
                ],
            )
        ]
    )

    citations = _source_citations(response)

    assert [citation.model_dump() for citation in citations] == [
        {"title": "source attr", "url": "https://example.test/a"},
        {"title": "annotation attr", "url": "https://example.test/b"},
    ]
