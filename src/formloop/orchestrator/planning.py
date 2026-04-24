from __future__ import annotations

import logging

from ..schemas import AssumptionRecord, ProgressEventKind
from .narration import fallback_plan
from .phase_context import OrchestrationPhaseContext, PhaseRuntimeContext

logger = logging.getLogger(__name__)


async def plan_phase(
    ctx: OrchestrationPhaseContext,
    runtime: PhaseRuntimeContext,
):
    run = runtime.run
    logger.info("plan phase: start")
    plan = await ctx.plan(runtime.user_prompt, runtime.profile)
    fresh = ctx.load_run(run.run_name)
    fresh.current_spec = plan.normalized_spec.model_dump()
    fresh.assumptions = [
        AssumptionRecord(topic=a.topic, assumption=a.assumption) for a in plan.assumptions
    ]
    ctx.save_run(fresh)
    spec_kind = plan.normalized_spec.type
    logger.info(
        "plan phase: complete kind=%s assumptions=%d topics=%d",
        spec_kind,
        len(plan.assumptions),
        len(plan.research_topics),
    )
    ctx.emit(
        run.run_name,
        ProgressEventKind.spec_normalized,
        message="spec normalized",
        data={
            "assumption_count": len(plan.assumptions),
            "research_topic_count": len(plan.research_topics),
            "design_brief": plan.design_brief,
            "spec_kind": spec_kind,
        },
    )
    for a in plan.assumptions:
        ctx.emit(
            run.run_name,
            ProgressEventKind.assumption_recorded,
            message=f"assumption: {a.topic}",
            data={"topic": a.topic, "assumption": a.assumption},
        )
    await ctx.narrate(
        run.run_name,
        phase="plan",
        just_completed="normalized the spec",
        next_step=(
            "kick off background research"
            if plan.research_topics
            else "hand the spec to the CAD designer"
        ),
        why="",
        signals={
            "assumptions": len(plan.assumptions),
            "research_topics": len(plan.research_topics),
        },
        context={
            "design_brief": plan.design_brief,
            "assumptions": [
                {"topic": a.topic, "assumption": a.assumption} for a in plan.assumptions[:4]
            ],
            "research_topics": list(plan.research_topics[:4]),
        },
        fallback=fallback_plan(plan),
    )
    return plan
