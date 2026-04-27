from __future__ import annotations

import asyncio
import logging

from ..schemas import ProgressEventKind
from .narration import fallback_research
from .phase_context import OrchestrationPhaseContext, PhaseRuntimeContext

logger = logging.getLogger(__name__)


async def research_phase(
    ctx: OrchestrationPhaseContext,
    runtime: PhaseRuntimeContext,
    *,
    plan,
) -> list[dict]:
    run = runtime.run
    if not plan.research_topics:
        logger.info("research phase: skipped (no topics)")
        return []
    logger.info("research phase: start topics=%d", len(plan.research_topics))
    ctx.emit(
        run.run_name,
        ProgressEventKind.research_started,
        message=f"researching {len(plan.research_topics)} topics",
        data={"topics": list(plan.research_topics)},
    )
    profile = (
        runtime.profile_for("research") if hasattr(runtime, "profile_for") else runtime.profile
    )
    tasks = [ctx.research_topic(topic, profile) for topic in plan.research_topics]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    findings: list[dict] = []
    failures = 0
    for topic, res in zip(plan.research_topics, results, strict=True):
        if isinstance(res, BaseException):
            failures += 1
            logger.warning(
                "research topic failed: topic=%r error=%s: %s",
                topic,
                type(res).__name__,
                res,
            )
            findings.append(
                {"topic": topic, "summary": f"[research failed: {res}]", "citations": []}
            )
            continue
        findings.append(res)
    logger.info("research phase: complete findings=%d failures=%d", len(findings), failures)

    fresh = ctx.load_run(run.run_name)
    fresh.research_findings = findings
    ctx.save_run(fresh)

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
