"""Deterministic run driver — the outer orchestration loop.

REQ: FLH-F-001, FLH-F-002, FLH-F-005, FLH-F-008, FLH-F-009, FLH-F-017,
REQ: FLH-F-018, FLH-F-019, FLH-F-020, FLH-F-022, FLH-F-024, FLH-F-026,
REQ: FLH-NF-005, FLH-NF-009, FLH-NF-010, FLH-D-011, FLH-D-012, FLH-D-013,
REQ: FLH-D-025
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from ..agents import (
    NarrationInput,
    RunContext,
    Runner,
    build_cad_designer,
    build_manager_final,
    build_manager_plan,
    build_reviewer,
)
from ..agents.manager import ManagerFinalAnswer
from ..config.profiles import HarnessConfig, Profile, validate_reasoning
from ..logging_util import setup_run_logger, teardown_run_logger
from ..schemas import (
    AgentAnswer,
    EffectiveRuntime,
    ProgressEvent,
    ProgressEventKind,
    RoleRuntime,
    RunStatus,
)
from ..store import RunStore
from .direct_research import research_topic_direct
from .narration import sanitize_context
from .narrator import Narrator
from .phase_context import PhaseRuntimeContext
from .planning import plan_phase
from .research import research_phase
from .revision_loop import revision_loop_phase
from .tool_trace import AgentToolTraceRecorder, write_tool_trace

logger = logging.getLogger(__name__)


@dataclass
class DriveRequest:
    prompt: str
    profile_name: str | None = None
    model_override: str | None = None
    reasoning_override: str | None = None
    reference_image: str | None = None
    max_revisions: int | None = None
    role_model_overrides: dict[str, str] | None = None
    role_reasoning_overrides: dict[str, str] | None = None


class RunDriver:
    """Drives a single run through plan → research → revision loop → final."""

    def __init__(
        self,
        config: HarnessConfig,
        *,
        store: RunStore | None = None,
        event_hook: Callable[[ProgressEvent], None] | None = None,
        narrator: Narrator | None = None,
    ) -> None:
        self.config = config
        self.store = store or RunStore(config.runs_dir)
        self._event_hook = event_hook
        self.narrator = narrator

    def create_shell(self, request: DriveRequest):
        profile = self.config.profile(request.profile_name)
        role_profiles = self.config.resolve_role_profiles(
            profile,
            global_model=request.model_override,
            global_reasoning=request.reasoning_override,
            role_model_overrides=request.role_model_overrides,
            role_reasoning_overrides=request.role_reasoning_overrides,
        )
        effective_model = request.model_override or profile.model
        effective_reasoning = (
            validate_reasoning(request.reasoning_override, label="global reasoning override")
            if request.reasoning_override
            else profile.reasoning
        )
        max_revisions = request.max_revisions or self.config.max_revisions
        run, layout = self.store.create_run(
            input_summary=request.prompt,
            effective_runtime=EffectiveRuntime(
                profile=profile.name,
                model=effective_model,
                reasoning=effective_reasoning,
                roles={
                    role: RoleRuntime(model=role_profile.model, reasoning=role_profile.reasoning)
                    for role, role_profile in role_profiles.items()
                },
            ),
            reference_image=request.reference_image,
        )
        run.status = RunStatus.running
        self.store.save_run(run)
        source_dir = layout.root / "_work" / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        run_ctx = RunContext(
            run_name=run.run_name,
            run_root=layout.root,
            source_dir=source_dir,
            profile=Profile(
                name=profile.name,
                model=effective_model,
                reasoning=effective_reasoning,
                description=profile.description,
                role_overrides=profile.role_overrides,
            ),
            timeouts=self.config.timeouts,
        )
        return run, run_ctx, run_ctx.profile, role_profiles, max_revisions

    async def run(self, request: DriveRequest) -> dict[str, Any]:
        run, run_ctx, profile, role_profiles, max_revisions = self.create_shell(request)
        return await self.continue_run(
            run=run,
            run_ctx=run_ctx,
            profile=profile,
            role_profiles=role_profiles,
            max_revisions=max_revisions,
            user_prompt=request.prompt,
        )

    async def continue_run(
        self,
        *,
        run,
        run_ctx: RunContext,
        profile: Profile,
        role_profiles: dict[str, Profile],
        max_revisions: int,
        user_prompt: str,
    ) -> dict[str, Any]:
        delivered_rev_name: str | None = None
        runtime = PhaseRuntimeContext(
            run=run,
            run_ctx=run_ctx,
            profile=profile,
            role_profiles=role_profiles,
            user_prompt=user_prompt,
        )
        if self.narrator is None:
            self.narrator = Narrator.auto(profile=runtime.profile_for("narrator"))
        log_handler = setup_run_logger(self.store.layout(run.run_name).log_path)
        start = time.monotonic()
        logger.info(
            "run start: name=%s profile=%s model=%s reasoning=%s max_revisions=%d prompt=%r",
            run.run_name,
            profile.name,
            profile.model,
            profile.reasoning,
            max_revisions,
            user_prompt[:200],
        )
        try:
            try:
                plan = await plan_phase(
                    self,
                    runtime,
                    max_research_topics=self.config.max_research_topics,
                )
                findings = await research_phase(
                    self,
                    runtime,
                    plan=plan,
                )
                delivered_rev_name = await revision_loop_phase(
                    self,
                    runtime,
                    plan=plan,
                    findings=findings,
                    max_revisions=max_revisions,
                )
                final = await self._finalize(
                    run, plan, delivered_rev_name, runtime.profile_for("manager_final")
                )
                run = self.store.load_run(run.run_name)
                run.final_answer = AgentAnswer(
                    text=final.text, delivered_revision_name=delivered_rev_name
                )
                run.status = RunStatus.succeeded if delivered_rev_name else RunStatus.failed
                if not delivered_rev_name:
                    if run.revisions:
                        run.status_detail = (
                            f"{len(run.revisions)} revision(s) persisted but none passed review"
                        )
                    else:
                        run.status_detail = "no revision bundle was delivered"
                self.store.save_run(run)
                self.emit(
                    run.run_name,
                    ProgressEventKind.delivered,
                    message=f"run {run.run_name} delivered",
                    data={"revision": delivered_rev_name, "status": run.status.value},
                )
                logger.info(
                    "run end: name=%s status=%s delivered=%s elapsed=%.2fs",
                    run.run_name,
                    run.status.value,
                    delivered_rev_name,
                    time.monotonic() - start,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "run failed: name=%s elapsed=%.2fs", run.run_name, time.monotonic() - start
                )
                run = self.store.load_run(run.run_name)
                run.status = RunStatus.failed
                run.status_detail = f"{type(exc).__name__}: {exc}"[:500]
                self.store.save_run(run)
                self.emit(
                    run.run_name,
                    ProgressEventKind.run_failed,
                    message=f"run failed: {exc}",
                    data={"error_type": type(exc).__name__},
                )
                raise
        finally:
            teardown_run_logger(log_handler)

        return {
            "run_name": run.run_name,
            "run_id": run.run_id,
            "status": run.status.value,
            "delivered_revision": delivered_rev_name,
            "final_answer": run.final_answer.text if run.final_answer else None,
        }

    async def _finalize(
        self, run, plan, delivered_rev_name: str | None, profile: Profile
    ) -> ManagerFinalAnswer:
        fresh = self.store.load_run(run.run_name)
        snap = self.store.load_snapshot(run.run_name)
        payload = {
            "spec": plan.normalized_spec.model_dump(),
            "delivered_revision": delivered_rev_name,
            "revisions": fresh.revisions,
            "latest_review_decision": (
                snap.latest_review_decision.value if snap.latest_review_decision else None
            ),
            "assumptions": [a.model_dump() for a in fresh.assumptions],
        }
        return await self.finalize(payload, profile)

    # phase context interface
    def emit(
        self,
        run_name: str,
        kind: ProgressEventKind,
        message: str,
        *,
        data: dict | None = None,
        phase: str | None = None,
        narration_error: str | None = None,
    ) -> None:
        event = ProgressEvent(
            index=0,
            kind=kind,
            message=message,
            phase=phase,
            narration_error=narration_error,
            data=data or {},
        )
        written = self.store.append_event(run_name, event)
        if self._event_hook is not None:
            try:
                self._event_hook(written)
            except Exception:
                pass

    async def narrate(
        self,
        run_name: str,
        *,
        phase: str,
        just_completed: str,
        next_step: str,
        why: str,
        signals: dict[str, Any],
        fallback: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        payload = NarrationInput(
            phase=phase,
            just_completed=just_completed,
            next_step=next_step,
            why=why,
            signals=dict(signals),
            context=sanitize_context(context or {}),
        )
        try:
            narrator = self.narrator or Narrator.auto()
            text, err = await narrator.narrate(payload, fallback=fallback)
        except Exception as exc:  # noqa: BLE001
            text, err = fallback, f"{type(exc).__name__}: {exc}"[:200]
        self.emit(
            run_name,
            ProgressEventKind.narration,
            text,
            data={"phase": phase, "signals": dict(signals), "narration_error": err},
            phase=phase,
            narration_error=err,
        )

    def load_run(self, run_name: str):
        return self.store.load_run(run_name)

    def save_run(self, run) -> None:
        self.store.save_run(run)

    def attach_review(self, run, revision_name: str, review) -> None:
        self.store.attach_review(run, revision_name, review)

    def persist_revision(self, run, bundle):
        return self.store.persist_revision(run, bundle)

    def load_snapshot(self, run_name: str):
        return self.store.load_snapshot(run_name)

    async def plan(self, prompt: str, profile: Profile):
        agent = build_manager_plan(profile)
        start = time.monotonic()
        logger.info("agent start: manager_planner timeout=%ss", self.config.timeouts.agent_run)
        result = await asyncio.wait_for(
            Runner.run(
                agent,
                input=(
                    f"User prompt:\n{prompt}\n\n"
                    "Return a ManagerPlan normalizing this into a concrete spec."
                ),
            ),
            timeout=self.config.timeouts.agent_run,
        )
        logger.info("agent end: manager_planner elapsed=%.2fs", time.monotonic() - start)
        return result.final_output

    async def research_topic(self, topic: str, profile: Profile) -> dict[str, Any]:
        start = time.monotonic()
        logger.info(
            "direct research start: timeout=%ss topic=%r model=%s reasoning=%s",
            self.config.timeouts.agent_run,
            topic[:160],
            profile.model,
            profile.reasoning,
        )
        finding = await research_topic_direct(
            topic,
            profile,
            timeout=self.config.timeouts.agent_run,
        )
        logger.info(
            "direct research end: elapsed=%.2fs topic=%r",
            time.monotonic() - start,
            topic[:160],
        )
        return finding

    async def design_revision(self, designer_input: str, run_ctx: RunContext, profile: Profile):
        designer_agent = build_cad_designer(profile, run_ctx)
        start = time.monotonic()
        recorder = AgentToolTraceRecorder(
            agent_name="cad_designer",
            model=profile.model,
            reasoning=profile.reasoning,
            max_turns=self.config.max_cad_designer_turns,
        )
        logger.info(
            "agent start: cad_designer timeout=%ss max_turns=%d",
            self.config.timeouts.agent_run,
            self.config.max_cad_designer_turns,
        )
        revision_attempt = int(run_ctx.notes.get("revision_attempt", 0) or 0)
        source_attempt = int(run_ctx.notes.get("source_attempt", 1) or 1)
        trace_path = (
            run_ctx.run_root
            / "_work"
            / "tool_traces"
            / f"cad_designer-r{revision_attempt:03d}-s{source_attempt:03d}.json"
        )
        try:
            result = await asyncio.wait_for(
                Runner.run(
                    designer_agent,
                    input=designer_input,
                    context=run_ctx,
                    max_turns=self.config.max_cad_designer_turns,
                    hooks=recorder,
                ),
                timeout=self.config.timeouts.agent_run,
            )
        except Exception as exc:
            trace = recorder.trace_from_error(exc)
            write_tool_trace(trace_path, trace)
            self._emit_cad_tool_summary(run_ctx, trace_path, trace)
            logger.info("agent error: cad_designer elapsed=%.2fs", time.monotonic() - start)
            raise
        trace = recorder.trace_from_result(result)
        write_tool_trace(trace_path, trace)
        self._emit_cad_tool_summary(run_ctx, trace_path, trace)
        logger.info("agent end: cad_designer elapsed=%.2fs", time.monotonic() - start)
        return result.final_output

    def _emit_cad_tool_summary(
        self, run_ctx: RunContext, trace_path, trace: dict[str, Any]
    ) -> None:
        summary_message = (
            "cad_designer tool calls: "
            + ", ".join(f"{name}={count}" for name, count in trace["counts"].items())
            if trace["counts"]
            else "cad_designer tool calls: 0"
        )
        self.emit(
            run_ctx.run_name,
            ProgressEventKind.agent_tool_summary,
            message=summary_message,
            data={
                "agent": "cad_designer",
                "total_tool_calls": trace["total_tool_calls"],
                "counts": trace["counts"],
                "trace_path": str(trace_path),
            },
        )

    async def review_revision(self, payload: list[dict[str, Any]], profile: Profile):
        reviewer = build_reviewer(profile)
        start = time.monotonic()
        logger.info("agent start: reviewer timeout=%ss", self.config.timeouts.agent_run)
        result = await asyncio.wait_for(
            Runner.run(reviewer, input=cast(Any, payload)),
            timeout=self.config.timeouts.agent_run,
        )
        logger.info("agent end: reviewer elapsed=%.2fs", time.monotonic() - start)
        return result.final_output

    async def finalize(self, payload: dict[str, Any], profile: Profile) -> ManagerFinalAnswer:
        agent = build_manager_final(profile)
        start = time.monotonic()
        logger.info("agent start: manager_final timeout=%ss", self.config.timeouts.agent_run)
        result = await asyncio.wait_for(
            Runner.run(
                agent,
                input=(
                    "Synthesize the final user-facing answer. Payload:\n\n"
                    + json.dumps(payload, indent=2, default=str)
                ),
            ),
            timeout=self.config.timeouts.agent_run,
        )
        logger.info("agent end: manager_final elapsed=%.2fs", time.monotonic() - start)
        return result.final_output


async def drive_run(
    prompt: str,
    *,
    config: HarnessConfig,
    profile: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    reference_image: str | None = None,
    max_revisions: int | None = None,
    role_model_overrides: dict[str, str] | None = None,
    role_reasoning_overrides: dict[str, str] | None = None,
    event_hook: Callable[[ProgressEvent], None] | None = None,
    narrator: Narrator | None = None,
) -> dict[str, Any]:
    driver = RunDriver(config, event_hook=event_hook, narrator=narrator)
    return await driver.run(
        DriveRequest(
            prompt=prompt,
            profile_name=profile,
            model_override=model,
            reasoning_override=effort,
            reference_image=reference_image,
            max_revisions=max_revisions,
            role_model_overrides=role_model_overrides,
            role_reasoning_overrides=role_reasoning_overrides,
        )
    )
