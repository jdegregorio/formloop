from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from formloop.agents.manager import ManagerPlan, NormalizedSpec
from formloop.orchestrator.planning import plan_phase
from formloop.orchestrator.research import research_phase
from formloop.schemas import ProgressEventKind

pytestmark = pytest.mark.asyncio


class _FakeCtx:
    def __init__(self, *, plan: ManagerPlan):
        self._plan = plan
        self.events: list[tuple[ProgressEventKind, str, dict]] = []
        self.run = SimpleNamespace(run_name="run-0001", research_findings=[])

    async def plan(self, prompt: str, profile) -> ManagerPlan:  # noqa: ARG002
        return self._plan

    async def narrate(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def emit(self, run_name, kind, message, *, data=None, phase=None, narration_error=None):  # noqa: ANN001, ANN002, ANN003, ARG002
        self.events.append((kind, message, data or {}))

    def load_run(self, run_name):  # noqa: ANN001, ARG002
        return self.run

    def save_run(self, run) -> None:  # noqa: ANN001
        self.run = run

    async def research_topic(self, topic: str, profile):  # noqa: ARG002
        return {"topic": topic, "summary": f"ok:{topic}", "citations": []}


def _plan_with_topics(count: int) -> ManagerPlan:
    return ManagerPlan(
        normalized_spec=NormalizedSpec(
            name="part",
            type="component",
            units="mm",
            design_intent="test",
            features=[],
            interfaces=[],
            constraints=[],
            preferences=[],
            key_dimension_parameters={},
        ),
        assumptions=[],
        research_topics=[f"topic-{i}" for i in range(count)],
        design_brief="brief",
    )


async def test_plan_phase_truncates_excess_research_topics() -> None:
    ctx = _FakeCtx(plan=_plan_with_topics(5))
    runtime = SimpleNamespace(
        run=SimpleNamespace(run_name="run-0001"),
        profile=SimpleNamespace(name="dev_test"),
        user_prompt="make a test part",
    )

    plan = await plan_phase(ctx, runtime, max_research_topics=3)

    assert plan.research_topics == ["topic-0", "topic-1", "topic-2"]
    truncate_events = [
        ev for ev in ctx.events if ev[0] is ProgressEventKind.research_topics_truncated
    ]
    assert len(truncate_events) == 1
    _, _, data = truncate_events[0]
    assert data == {"requested_count": 5, "kept_count": 3, "dropped_count": 2}


async def test_research_phase_keeps_order() -> None:
    ctx = _FakeCtx(plan=_plan_with_topics(6))
    runtime = SimpleNamespace(
        run=SimpleNamespace(run_name="run-0001"),
        profile=SimpleNamespace(name="dev_test"),
    )

    async def bounded_topic(topic: str, profile):  # noqa: ARG001
        await asyncio.sleep(0.02)
        return {"topic": topic, "summary": f"ok:{topic}", "citations": []}

    ctx.research_topic = bounded_topic
    findings = await research_phase(
        ctx,
        runtime,
        plan=ctx._plan,
    )

    assert [f["topic"] for f in findings] == ctx._plan.research_topics


async def test_research_phase_keeps_stable_order_when_some_topics_fail() -> None:
    ctx = _FakeCtx(plan=_plan_with_topics(4))
    runtime = SimpleNamespace(
        run=SimpleNamespace(run_name="run-0001"),
        profile=SimpleNamespace(name="dev_test"),
    )

    async def sometimes_fails(topic: str, profile):  # noqa: ARG001
        if topic == "topic-1":
            raise RuntimeError("boom")
        await asyncio.sleep(0.01)
        return {"topic": topic, "summary": f"ok:{topic}", "citations": []}

    ctx.research_topic = sometimes_fails
    findings = await research_phase(
        ctx,
        runtime,
        plan=ctx._plan,
    )

    assert [f["topic"] for f in findings] == ctx._plan.research_topics
    assert findings[1]["summary"].startswith("[research failed:")
    assert findings[1]["citations"] == []
