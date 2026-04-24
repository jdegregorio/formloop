from __future__ import annotations

import asyncio

from ..schemas import ProgressEventKind
from .narration import fallback_research
from .phase_context import OrchestrationPhaseContext, PhaseRuntimeContext


async def research_phase(
    ctx: OrchestrationPhaseContext,
    runtime: PhaseRuntimeContext,
    *,
    plan,
) -> list[dict]:
    run = runtime.run
    if not plan.research_topics:
        return []
    ctx.emit(
        run.run_name,
        ProgressEventKind.research_started,
        message=f"researching {len(plan.research_topics)} topics",
        data={"topics": list(plan.research_topics)},
    )
    tasks = [ctx.research_topic(topic, runtime.profile) for topic in plan.research_topics]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    findings: list[dict] = []
    failures = 0
    for topic, res in zip(plan.research_topics, results, strict=True):
        if isinstance(res, BaseException):
            failures += 1
            findings.append(
                {"topic": topic, "summary": f"[research failed: {res}]", "citations": []}
            )
            continue
        findings.append(res)
    ctx.emit(
        run.run_name,
        ProgressEventKind.research_completed,
        message="research complete",
        data={"count": len(findings)},
    )
    await ctx.narrate(
        run.run_name,
        phase="research",
        just_completed="finished the research lookups",
        next_step="hand the findings + spec to the CAD designer",
        why=(
            f"{failures} of {len(findings)} lookups failed but we have enough to proceed"
            if failures
            else ""
        ),
        signals={"findings": len(findings), "failures": failures},
        context={
            "research_findings": [
                {"topic": f.get("topic", ""), "summary": (f.get("summary", "") or "")[:280]}
                for f in findings[:4]
            ]
        },
        fallback=fallback_research(findings, failures),
    )
    return findings
