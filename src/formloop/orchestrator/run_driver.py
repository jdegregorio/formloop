"""Deterministic run driver — the outer orchestration loop.

REQ: FLH-F-001, FLH-F-002, FLH-F-005, FLH-F-008, FLH-F-009, FLH-F-017,
REQ: FLH-F-018, FLH-F-019, FLH-F-020, FLH-F-022, FLH-F-024, FLH-F-026,
REQ: FLH-NF-005, FLH-NF-009, FLH-NF-010, FLH-D-011, FLH-D-012, FLH-D-013,
REQ: FLH-D-025
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..agents import (
    NarrationInput,
    PromptContext,
    RunContext,
    Runner,
    build_cad_designer,
    build_design_researcher,
    build_manager_final,
    build_manager_plan,
    build_quality_specialist_review,
)
from ..agents.cad_designer import CadRevisionResult
from ..agents.manager import ManagerFinalAnswer, ManagerPlan
from ..config.profiles import HarnessConfig, Profile
from ..schemas import (
    AgentAnswer,
    AssumptionRecord,
    EffectiveRuntime,
    ProgressEvent,
    ProgressEventKind,
    ReviewDecision,
    ReviewSummary,
    Revision,
    RevisionTrigger,
    RunStatus,
)
from ..store import RunStore
from ..store.run_store import CandidateBundle
from .narrator import Narrator


@dataclass
class DriveRequest:
    prompt: str
    profile_name: str | None = None
    reference_image: str | None = None
    max_revisions: int | None = None


def _staging_views_dir(run_root: Path, attempt: int) -> Path:
    out = run_root / "_work" / f"views_{attempt:03d}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _stage_views(render_out: Path, staging: Path) -> list[Path]:
    names = ("front", "back", "left", "right", "top", "bottom", "iso")
    staged: list[Path] = []
    for name in names:
        src = render_out / f"{name}.png"
        if src.is_file():
            dst = staging / src.name
            dst.write_bytes(src.read_bytes())
            staged.append(dst)
    return staged


def _write_inspect_json(run_root: Path, attempt: int, payload: dict | None) -> Path | None:
    if not payload:
        return None
    path = run_root / "_work" / f"inspect_{attempt:03d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return path


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
        self.narrator = narrator if narrator is not None else Narrator.auto()

    # ---- public API ------------------------------------------------------

    def create_shell(self, request: DriveRequest):
        """Create the run shell eagerly and return (run, run_ctx, profile, max_revisions).

        Splitting this out lets the HTTP API return a run name before the
        long-running loop starts.
        """

        profile = self.config.profile(request.profile_name)
        max_revisions = request.max_revisions or self.config.max_revisions
        run, layout = self.store.create_run(
            input_summary=request.prompt,
            effective_runtime=EffectiveRuntime(
                profile=profile.name, model=profile.model, reasoning=profile.reasoning
            ),
            reference_image=request.reference_image,
        )
        run.status = RunStatus.running
        self.store.save_run(run)
        run_ctx = RunContext(
            run_name=run.run_name,
            run_root=layout.root,
            inputs_dir=layout.inputs_dir,
            profile=profile,
        )
        return run, run_ctx, profile, max_revisions

    async def run(self, request: DriveRequest) -> dict[str, Any]:
        run, run_ctx, profile, max_revisions = self.create_shell(request)
        return await self.continue_run(
            run=run,
            run_ctx=run_ctx,
            profile=profile,
            max_revisions=max_revisions,
            user_prompt=request.prompt,
        )

    async def continue_run(
        self,
        *,
        run,
        run_ctx: RunContext,
        profile: Profile,
        max_revisions: int,
        user_prompt: str,
    ) -> dict[str, Any]:
        delivered_rev_name: str | None = None
        try:
            plan = await self._plan(run, user_prompt, profile)
            findings = await self._research(run, plan, profile)
            delivered_rev_name = await self._revision_loop(
                run=run,
                run_ctx=run_ctx,
                plan=plan,
                findings=findings,
                profile=profile,
                max_revisions=max_revisions,
                user_prompt=user_prompt,
            )
            final = await self._finalize(run, plan, delivered_rev_name, profile)
            run = self.store.load_run(run.run_name)
            run.final_answer = AgentAnswer(
                text=final.text,
                delivered_revision_name=delivered_rev_name,
            )
            run.status = (
                RunStatus.succeeded if delivered_rev_name else RunStatus.failed
            )
            if not delivered_rev_name:
                run.status_detail = "no revision bundle was delivered"
            self.store.save_run(run)
            self._emit(
                run.run_name,
                ProgressEventKind.delivered,
                message=f"run {run.run_name} delivered",
                data={"revision": delivered_rev_name, "status": run.status.value},
            )
        except Exception as exc:  # noqa: BLE001 — top-level reporting
            run = self.store.load_run(run.run_name)
            run.status = RunStatus.failed
            run.status_detail = f"{type(exc).__name__}: {exc}"[:500]
            self.store.save_run(run)
            self._emit(
                run.run_name,
                ProgressEventKind.run_failed,
                message=f"run failed: {exc}",
                data={"error_type": type(exc).__name__},
            )
            raise

        return {
            "run_name": run.run_name,
            "run_id": run.run_id,
            "status": run.status.value,
            "delivered_revision": delivered_rev_name,
            "final_answer": run.final_answer.text if run.final_answer else None,
        }

    # ---- phases ----------------------------------------------------------

    async def _plan(self, run, prompt: str, profile: Profile) -> ManagerPlan:
        await self._narrate(
            run.run_name,
            phase="plan",
            just_completed="received the user prompt",
            next_step="normalize it into a concrete spec",
            why="we want a structured target before any CAD work starts",
            signals={},
            fallback="planning the spec",
        )
        agent = build_manager_plan(profile)
        result = await Runner.run(
            agent,
            input=(
                f"User prompt:\n{prompt}\n\n"
                "Return a ManagerPlan normalizing this into a concrete spec."
            ),
        )
        plan: ManagerPlan = result.final_output
        fresh = self.store.load_run(run.run_name)
        fresh.current_spec = dict(plan.normalized_spec)
        fresh.assumptions = [
            AssumptionRecord(topic=a.topic, assumption=a.assumption)
            for a in plan.assumptions
        ]
        self.store.save_run(fresh)
        self._emit(
            run.run_name,
            ProgressEventKind.spec_normalized,
            message="spec normalized",
            data={
                "assumption_count": len(plan.assumptions),
                "research_topic_count": len(plan.research_topics),
            },
        )
        for a in plan.assumptions:
            self._emit(
                run.run_name,
                ProgressEventKind.assumption_recorded,
                message=f"assumption: {a.topic}",
                data={"topic": a.topic, "assumption": a.assumption},
            )
        await self._narrate(
            run.run_name,
            phase="plan",
            just_completed="normalized the spec",
            next_step=(
                "kick off background research"
                if plan.research_topics
                else "hand the spec to the CAD designer"
            ),
            why=(
                "we recorded a few assumptions where the prompt was ambiguous"
                if plan.assumptions
                else ""
            ),
            signals={
                "assumptions": len(plan.assumptions),
                "research_topics": len(plan.research_topics),
            },
            fallback="spec normalized",
        )
        return plan

    async def _research(self, run, plan: ManagerPlan, profile: Profile) -> list[dict]:
        if not plan.research_topics:
            return []
        self._emit(
            run.run_name,
            ProgressEventKind.research_started,
            message=f"researching {len(plan.research_topics)} topics",
            data={"topics": list(plan.research_topics)},
        )
        await self._narrate(
            run.run_name,
            phase="research",
            just_completed="planned the research topics",
            next_step=(
                f"look up {len(plan.research_topics)} topic"
                f"{'s' if len(plan.research_topics) != 1 else ''} in parallel"
            ),
            why="parallel lookups keep the run snappy",
            signals={"topic_count": len(plan.research_topics)},
            fallback=f"researching {len(plan.research_topics)} topics",
        )
        researcher = build_design_researcher(profile)
        tasks = [Runner.run(researcher, input=topic) for topic in plan.research_topics]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        findings: list[dict] = []
        failures = 0
        for topic, res in zip(plan.research_topics, results, strict=True):
            if isinstance(res, Exception):
                failures += 1
                findings.append(
                    {"topic": topic, "summary": f"[research failed: {res}]", "citations": []}
                )
                continue
            findings.append(res.final_output.model_dump())
        self._emit(
            run.run_name,
            ProgressEventKind.research_completed,
            message="research complete",
            data={"count": len(findings)},
        )
        await self._narrate(
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
            fallback="research complete",
        )
        return findings

    async def _revision_loop(
        self,
        *,
        run,
        run_ctx: RunContext,
        plan: ManagerPlan,
        findings: list[dict],
        profile: Profile,
        max_revisions: int,
        user_prompt: str,
    ) -> str | None:
        prior_review: dict | None = None
        delivered: str | None = None

        for attempt in range(1, max_revisions + 1):
            self._emit(
                run.run_name,
                ProgressEventKind.revision_started,
                message=f"revision attempt {attempt}",
                data={"attempt": attempt},
            )
            await self._narrate(
                run.run_name,
                phase="revision",
                just_completed=(
                    "reviewed the prior attempt"
                    if prior_review is not None
                    else "got the spec ready"
                ),
                next_step=(
                    f"build revision attempt {attempt}"
                    if attempt > 1
                    else "build the first revision"
                ),
                why=(
                    "the reviewer asked us to iterate"
                    if prior_review is not None
                    else "we always try at least one design pass"
                ),
                signals={"attempt": attempt, "max_attempts": max_revisions},
                fallback=f"starting revision attempt {attempt}",
            )
            prompt_ctx = PromptContext(
                input_summary=user_prompt,
                current_spec=plan.normalized_spec,
                assumptions=[
                    {"topic": a.topic, "assumption": a.assumption} for a in plan.assumptions
                ],
                research_findings=findings,
                prior_review=prior_review,
            )
            designer_agent = build_cad_designer(profile)
            designer_input = (
                f"Design brief:\n{plan.design_brief}\n\n"
                f"Context (JSON):\n{prompt_ctx.to_prompt_text()}\n\n"
                "Author model.py, build, inspect, render, then return CadRevisionResult."
            )
            designer_run = await Runner.run(
                designer_agent, input=designer_input, context=run_ctx, max_turns=24
            )
            cad_out: CadRevisionResult = designer_run.final_output
            self._emit(
                run.run_name,
                ProgressEventKind.revision_built,
                message=(
                    f"designer returned build_ok={cad_out.build_ok} "
                    f"render_ok={cad_out.render_ok}"
                ),
                data={
                    "build_ok": cad_out.build_ok,
                    "inspect_ok": cad_out.inspect_ok,
                    "render_ok": cad_out.render_ok,
                    "dimensions": cad_out.dimensions,
                },
            )
            await self._narrate(
                run.run_name,
                phase="revision",
                just_completed="ran the CAD designer",
                next_step=(
                    "persist the revision and send it to review"
                    if cad_out.build_ok and cad_out.render_ok
                    else "retry — the build or render didn't complete cleanly"
                ),
                why="",
                signals={
                    "attempt": attempt,
                    "build_ok": cad_out.build_ok,
                    "render_ok": cad_out.render_ok,
                    "inspect_ok": cad_out.inspect_ok,
                },
                fallback=(
                    f"designer build_ok={cad_out.build_ok} render_ok={cad_out.render_ok}"
                ),
            )

            if not (
                cad_out.build_ok
                and cad_out.render_ok
                and run_ctx.notes.get("last_build")
                and run_ctx.notes.get("last_render")
            ):
                self._emit(
                    run.run_name,
                    ProgressEventKind.breadcrumb,
                    message="no full bundle this attempt; not persisting",
                    data={"attempt": attempt, "build_errors": cad_out.build_errors[:3]},
                )
                if attempt >= max_revisions:
                    break
                prior_review = {
                    "decision": "revise",
                    "revision_instructions": [
                        "Previous attempt did not produce a full build+render bundle.",
                        f"Errors: {cad_out.build_errors[:3]}",
                    ],
                }
                continue

            build_dir = Path(run_ctx.notes["last_build"]["output_dir"])
            render_dir = Path(run_ctx.notes["last_render"]["output_dir"])
            staging = _staging_views_dir(run_ctx.run_root, attempt)
            _stage_views(render_dir, staging)

            build_meta = build_dir / "build-metadata.json"
            render_meta = render_dir / "render-metadata.json"
            inspect_src = _write_inspect_json(
                run_ctx.run_root, attempt, run_ctx.notes.get("last_inspect")
            )

            bundle = CandidateBundle(
                trigger=(
                    RevisionTrigger.initial
                    if attempt == 1
                    else RevisionTrigger.review_revise
                ),
                spec_snapshot=dict(plan.normalized_spec),
                designer_notes=cad_out.revision_notes,
                known_risks=list(cad_out.known_risks),
                step_src=build_dir / "model.step",
                glb_src=build_dir / "model.glb",
                views_dir_src=staging,
                render_sheet_src=render_dir / "sheet.png",
                build_metadata_src=build_meta if build_meta.is_file() else None,
                render_metadata_src=render_meta if render_meta.is_file() else None,
                inspect_summary_src=inspect_src,
            )
            fresh = self.store.load_run(run.run_name)
            revision, _ = self.store.persist_revision(fresh, bundle)
            delivered = revision.revision_name
            self._emit(
                run.run_name,
                ProgressEventKind.revision_persisted,
                message=f"persisted {revision.revision_name}",
                data={"revision": revision.revision_name, "ordinal": revision.ordinal},
            )
            await self._narrate(
                run.run_name,
                phase="revision",
                just_completed="saved the candidate artifacts",
                next_step="hand it to the quality specialist for review",
                why="",
                signals={"attempt": attempt, "ordinal": revision.ordinal},
                fallback="revision saved; reviewing",
            )

            review = await self._review(
                run=run,
                plan=plan,
                cad_out=cad_out,
                run_ctx=run_ctx,
                profile=profile,
                revision=revision,
            )
            if review.decision == ReviewDecision.pass_:
                self._emit(
                    run.run_name,
                    ProgressEventKind.breadcrumb,
                    message="revision accepted",
                )
                await self._narrate(
                    run.run_name,
                    phase="revision",
                    just_completed="accepted the revision",
                    next_step="synthesize the final answer for the user",
                    why=(
                        "the reviewer is confident in this design"
                        if review.confidence and review.confidence >= 0.7
                        else "the reviewer is comfortable handing this off"
                    ),
                    signals={"confidence": review.confidence},
                    fallback="revision accepted",
                )
                break
            prior_review = review.model_dump()

        return delivered

    async def _review(
        self,
        *,
        run,
        plan: ManagerPlan,
        cad_out: CadRevisionResult,
        run_ctx: RunContext,
        profile: Profile,
        revision: Revision,
    ) -> ReviewSummary:
        self._emit(
            run.run_name,
            ProgressEventKind.review_started,
            message=f"reviewing {revision.revision_name}",
        )
        await self._narrate(
            run.run_name,
            phase="review",
            just_completed="finished the build and render",
            next_step="check the result against the spec",
            why="",
            signals={},
            fallback="reviewing the revision",
        )
        reviewer = build_quality_specialist_review(profile)
        payload = {
            "spec": plan.normalized_spec,
            "designer_notes": cad_out.revision_notes,
            "designer_dimensions": cad_out.dimensions,
            "known_risks": cad_out.known_risks,
            "inspect_summary": run_ctx.notes.get("last_inspect"),
            "render_sheet": "7-view composite (front/back/left/right/top/bottom/iso)",
        }
        reviewer_run = await Runner.run(
            reviewer,
            input=(
                "Review this revision and produce a ReviewSummary.\n\n"
                + json.dumps(payload, indent=2, default=str)
            ),
        )
        review: ReviewSummary = reviewer_run.final_output
        fresh = self.store.load_run(run.run_name)
        self.store.attach_review(fresh, revision.revision_name, review)
        self._emit(
            run.run_name,
            ProgressEventKind.review_completed,
            message=f"review decision: {review.decision.value}",
            data={
                "revision": revision.revision_name,
                "decision": review.decision.value,
                "confidence": review.confidence,
            },
        )
        await self._narrate(
            run.run_name,
            phase="review",
            just_completed="reviewed the revision",
            next_step=(
                "deliver this design"
                if review.decision == ReviewDecision.pass_
                else "iterate based on the review feedback"
            ),
            why=(
                review.key_findings[0]
                if review.key_findings
                else ""
            ),
            signals={
                "decision": review.decision.value,
                "confidence": review.confidence,
            },
            fallback=f"review decision: {review.decision.value}",
        )
        return review

    async def _finalize(
        self,
        run,
        plan: ManagerPlan,
        delivered_rev_name: str | None,
        profile: Profile,
    ) -> ManagerFinalAnswer:
        await self._narrate(
            run.run_name,
            phase="final",
            just_completed=(
                "settled on a design"
                if delivered_rev_name
                else "exhausted our revision attempts"
            ),
            next_step="write up what we delivered for the user",
            why="",
            signals={"delivered": bool(delivered_rev_name)},
            fallback="synthesizing the final answer",
        )
        fresh = self.store.load_run(run.run_name)
        snap = self.store.load_snapshot(run.run_name)
        payload = {
            "spec": plan.normalized_spec,
            "delivered_revision": delivered_rev_name,
            "revisions": fresh.revisions,
            "latest_review_decision": (
                snap.latest_review_decision.value if snap.latest_review_decision else None
            ),
            "assumptions": [a.model_dump() for a in fresh.assumptions],
        }
        agent = build_manager_final(profile)
        result = await Runner.run(
            agent,
            input=(
                "Synthesize the final user-facing answer. Payload:\n\n"
                + json.dumps(payload, indent=2, default=str)
            ),
        )
        return result.final_output

    # ---- helpers ---------------------------------------------------------

    def _emit(
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

    async def _narrate(
        self,
        run_name: str,
        *,
        phase: str,
        just_completed: str,
        next_step: str,
        why: str,
        signals: dict[str, Any],
        fallback: str,
    ) -> None:
        """Generate and emit a narration event.

        REQ: FLH-F-024, FLH-F-026, FLH-NF-010 — never aborts the run; on
        Narrator failure the static ``fallback`` is emitted with the error
        recorded in ``narration_error``.
        """

        payload = NarrationInput(
            phase=phase,
            just_completed=just_completed,
            next_step=next_step,
            why=why,
            signals=dict(signals),
        )
        try:
            text, err = await self.narrator.narrate(payload, fallback=fallback)
        except Exception as exc:  # noqa: BLE001 -- belt-and-suspenders
            text, err = fallback, f"{type(exc).__name__}: {exc}"[:200]
        self._emit(
            run_name,
            ProgressEventKind.narration,
            text,
            data={"phase": phase, "signals": dict(signals)},
            phase=phase,
            narration_error=err,
        )


async def drive_run(
    prompt: str,
    *,
    config: HarnessConfig,
    profile: str | None = None,
    reference_image: str | None = None,
    max_revisions: int | None = None,
    event_hook: Callable[[ProgressEvent], None] | None = None,
    narrator: Narrator | None = None,
) -> dict[str, Any]:
    driver = RunDriver(config, event_hook=event_hook, narrator=narrator)
    return await driver.run(
        DriveRequest(
            prompt=prompt,
            profile_name=profile,
            reference_image=reference_image,
            max_revisions=max_revisions,
        )
    )
