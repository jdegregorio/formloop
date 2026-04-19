"""Core harness orchestration service."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from agents import Agent, Runner

from ..agents.cad_designer import build_cad_designer_agent
from ..agents.common import (
    ExecutionTraceHooks,
    HarnessAgentContext,
    image_input_item,
    json_output_extractor,
    reasoning_settings,
    text_input_item,
    user_message,
)
from ..agents.design_researcher import build_design_researcher_agent
from ..agents.manager import build_manager_delivery_agent, build_manager_normalizer_agent
from ..agents.quality_specialist import build_quality_specialist_agent
from ..config import HarnessConfig, load_config
from ..jsonutil import utc_now
from ..models import (
    ArtifactSummaryItem,
    CadDesignOutput,
    ManagerNormalizationOutput,
    NormalizedSpec,
    ProgressEvent,
    ReviewDecision,
    ReviewSummary,
    RunCreateRequest,
    RunRecord,
    RunSnapshot,
    RunStatus,
)
from ..persistence import RunStore
from ..runtime.cad import CadBundle, CadCliRuntime
from ..runtime.source_validation import validate_cad_source


@dataclass(slots=True)
class HarnessOutcome:
    run: RunRecord
    snapshot: RunSnapshot
    final_message: str


class HarnessService:
    """Owns the deterministic outer loop for normal runs."""

    # Req: FLH-F-002, FLH-F-004, FLH-F-005, FLH-F-008, FLH-F-019, FLH-D-011

    def __init__(
        self,
        *,
        config: HarnessConfig | None = None,
        store: RunStore | None = None,
        cad_runtime: CadCliRuntime | None = None,
    ) -> None:
        self.config = config or load_config()
        self.store = store or RunStore(self.config.run_root_path())
        self.cad_runtime = cad_runtime or CadCliRuntime()

    def _progress_event(
        self,
        event_type: str,
        status: str,
        breadcrumb: str,
        **data: Any,
    ) -> ProgressEvent:
        return ProgressEvent(
            event_id=f"evt-{uuid4().hex[:10]}",
            event_type=event_type,
            status=status,
            breadcrumb=breadcrumb,
            data=data,
        )

    def _write_progress(self, run: RunRecord, snapshot: RunSnapshot, event: ProgressEvent) -> None:
        run.updated_at = utc_now()
        run.progress_events.append(event.event_id)
        self.store.append_event(run.run_name, event)
        self.store.write_run(run)
        self.store.write_snapshot(snapshot, run_name=run.run_name)

    def _create_placeholder_run(self, request: RunCreateRequest, profile_name: str) -> RunRecord:
        profile = self.config.profile(profile_name)
        return self.store.create_run(
            request,
            input_summary=request.prompt,
            current_spec=NormalizedSpec(intent_summary=request.prompt),
            effective_profile=profile_name,
            effective_model=profile.model,
            effective_reasoning=profile.reasoning,
        )

    def begin_run(self, request: RunCreateRequest) -> RunRecord:
        profile_name = request.profile or self.config.runtime.default_profile
        run = self._create_placeholder_run(request, profile_name)
        initial_snapshot = self._materialize_snapshot(run)
        self._write_progress(
            run,
            initial_snapshot,
            self._progress_event(
                "run_created",
                "ok",
                "Run created",
                run_id=run.run_id,
                run_name=run.run_name,
            ),
        )
        return run

    async def _runner_run(
        self,
        agent: Agent[HarnessAgentContext],
        payload: Any,
        *,
        context: HarnessAgentContext,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return await Runner.run(
                    agent,
                    payload,
                    context=context,
                    hooks=ExecutionTraceHooks(),
                )
            except Exception as exc:  # pragma: no cover - exercised in live UAT
                last_error = exc
                if attempt == 2:
                    raise
                await asyncio.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"agent run failed: {last_error}")

    async def _run_manager_normalization(
        self,
        *,
        request: RunCreateRequest,
        model: str,
        reasoning: str,
        context: HarnessAgentContext,
    ) -> ManagerNormalizationOutput:
        agent = build_manager_normalizer_agent(model=model, reasoning=reasoning)
        input_items = [
            user_message(
                text_input_item(
                    "Normalize this CAD request into a fit/form/function spec.\n"
                    f"Prompt: {request.prompt}\n"
                    f"Reference image: {request.reference_image or 'none'}"
                )
            )
        ]
        if request.reference_image:
            input_items[0]["content"].append(image_input_item(Path(request.reference_image)))
        result = await self._runner_run(agent, cast(Any, input_items), context=context)
        return cast(ManagerNormalizationOutput, result.final_output)

    async def _call_manager_tool(
        self,
        *,
        manager_name: str,
        manager_instructions: str,
        tool_agent: Agent[HarnessAgentContext],
        payload: dict[str, Any],
        model: str,
        reasoning: str,
        context: HarnessAgentContext,
    ) -> str:
        tool = tool_agent.as_tool(
            tool_name=tool_agent.name.lower().replace(" ", "_"),
            tool_description=tool_agent.handoff_description,
            custom_output_extractor=json_output_extractor,
        )
        manager = Agent[HarnessAgentContext](
            name=manager_name,
            instructions=manager_instructions,
            model=model,
            model_settings=reasoning_settings(reasoning, tool_choice="required"),
            tools=[tool],
            tool_use_behavior="stop_on_first_tool",
        )
        result = await self._runner_run(
            manager,
            json.dumps(payload, indent=2, sort_keys=True),
            context=context,
        )
        return cast(str, result.final_output)

    async def _design_revision_source(
        self,
        *,
        run: RunRecord,
        revision_ordinal: int,
        model: str,
        reasoning: str,
        context: HarnessAgentContext,
        prior_review: ReviewSummary | None,
    ) -> CadDesignOutput:
        designer = build_cad_designer_agent(model=model, reasoning=reasoning)
        payload = {
            "current_spec": run.current_spec.model_dump(mode="json"),
            "assumptions": run.assumptions,
            "research_findings": [
                finding.model_dump(mode="json") for finding in run.research_findings
            ],
            "revision_ordinal": revision_ordinal,
            "prior_review": prior_review.model_dump(mode="json") if prior_review else None,
        }
        raw = await self._call_manager_tool(
            manager_name="Manager Design Step",
            manager_instructions=(
                "You are the manager. Call the CAD Designer tool exactly once to produce the next "
                "candidate revision source. Do not answer directly."
            ),
            tool_agent=designer,
            payload=payload,
            model=model,
            reasoning=reasoning,
            context=context,
        )
        return CadDesignOutput.model_validate_json(raw)

    async def _review_revision(
        self,
        *,
        run: RunRecord,
        bundle: CadBundle,
        revision_dir: Path,
        model: str,
        reasoning: str,
        context: HarnessAgentContext,
        reference_image: str | None,
    ) -> ReviewSummary:
        reviewer = build_quality_specialist_agent(
            model=model,
            reasoning=reasoning,
            mode="normal_review",
        )
        payload = {
            "spec": run.current_spec.model_dump(mode="json"),
            "assumptions": run.assumptions,
            "deterministic_inspect_summary": bundle.inspect_summary,
            "artifact_manifest": bundle.manifest.model_dump(mode="json"),
        }
        content_items = [text_input_item(json.dumps(payload, indent=2, sort_keys=True))]
        render_sheet = revision_dir / "render-sheet.png"
        if render_sheet.exists():
            content_items.append(image_input_item(render_sheet))
        if reference_image:
            content_items.append(image_input_item(Path(reference_image)))
        result = await self._runner_run(
            reviewer,
            cast(Any, [user_message(*content_items)]),
            context=context,
        )
        return cast(ReviewSummary, result.final_output)

    async def _final_delivery_message(
        self,
        *,
        run: RunRecord,
        final_review: ReviewSummary | None,
        model: str,
        reasoning: str,
        context: HarnessAgentContext,
    ) -> str:
        manager = build_manager_delivery_agent(model=model, reasoning=reasoning)
        prompt = json.dumps(
            {
                "prompt": run.prompt,
                "run_name": run.run_name,
                "current_spec": run.current_spec.model_dump(mode="json"),
                "assumptions": run.assumptions,
                "final_review": final_review.model_dump(mode="json") if final_review else None,
                "artifacts": run.artifact_references,
            },
            indent=2,
            sort_keys=True,
        )
        result = await self._runner_run(manager, prompt, context=context)
        return str(result.final_output)

    def _materialize_snapshot(self, run: RunRecord, review_path: str | None = None) -> RunSnapshot:
        artifacts = [
            ArtifactSummaryItem(role=role, path=path)
            for role, path in sorted(run.artifact_references.items())
        ]
        return RunSnapshot(
            run_id=run.run_id,
            run_name=run.run_name,
            status=run.status,
            current_spec_summary=run.current_spec.intent_summary,
            latest_revision_id=run.current_revision_id,
            latest_review_summary_path=review_path,
            artifact_summary=artifacts,
            last_event_reference=run.progress_events[-1] if run.progress_events else None,
        )

    async def _execute_existing_run(
        self,
        *,
        request: RunCreateRequest,
        run: RunRecord,
        profile_name: str,
    ) -> HarnessOutcome:
        profile = self.config.profile(profile_name)
        context = HarnessAgentContext(run_id=run.run_id)

        normalization = await self._run_manager_normalization(
            request=request,
            model=profile.model,
            reasoning=profile.reasoning,
            context=context,
        )
        run.current_spec = normalization.current_spec
        run.input_summary = normalization.input_summary
        run.assumptions = normalization.assumptions
        run.current_status_summary = "Spec normalized"
        run.status = RunStatus.running
        self._write_progress(
            run,
            self._materialize_snapshot(run),
            self._progress_event(
                "spec_normalized",
                "ok",
                "Spec normalized and assumptions recorded",
                assumptions=run.assumptions,
                research_topics=[
                    topic.model_dump(mode="json") for topic in normalization.research_topics
                ],
            ),
        )

        run.research_findings = []
        if normalization.research_topics:
            self._write_progress(
                run,
                self._materialize_snapshot(run),
                self._progress_event(
                    "research_started",
                    "ok",
                    "Research started",
                    topic_count=len(normalization.research_topics),
                ),
            )
            researcher = build_design_researcher_agent(
                model=profile.model,
                reasoning=profile.reasoning,
            )

            async def research_one(topic: Any) -> Any:
                result = await self._runner_run(
                    researcher,
                    (
                        f"Research topic_id={topic.topic_id}\n"
                        f"Question: {topic.question}\n"
                        f"Reason: {topic.reason}"
                    ),
                    context=context,
                )
                return result.final_output

            run.research_findings = list(
                await asyncio.gather(
                    *(research_one(topic) for topic in normalization.research_topics)
                )
            )
            self.store.write_json_file(
                self.store.run_dir(run.run_name) / "research" / "research-findings.json",
                [finding.model_dump(mode="json") for finding in run.research_findings],
            )
            self._write_progress(
                run,
                self._materialize_snapshot(run),
                self._progress_event(
                    "research_completed",
                    "ok",
                    "Research completed",
                    findings=[finding.model_dump(mode="json") for finding in run.research_findings],
                ),
            )

        final_review: ReviewSummary | None = None
        prior_review: ReviewSummary | None = None

        for _ in range(profile.max_revisions):
            revision, revision_dir = self.store.create_revision(
                run=run,
                trigger="initial_design" if prior_review is None else "review_revision_request",
            )
            run.current_revision_id = revision.revision_id
            run.current_status_summary = f"Designing {revision.revision_name}"
            self._write_progress(
                run,
                self._materialize_snapshot(run),
                self._progress_event(
                    "revision_started",
                    "ok",
                    f"Revision {revision.revision_name} started",
                    revision_id=revision.revision_id,
                    revision_name=revision.revision_name,
                ),
            )

            design_output: CadDesignOutput | None = None
            bundle: CadBundle | None = None
            build_error: str | None = None

            for build_attempt in range(self.config.runtime.build_repair_attempts + 1):
                design_output = await self._design_revision_source(
                    run=run,
                    revision_ordinal=revision.ordinal,
                    model=profile.model,
                    reasoning=profile.reasoning,
                    context=context,
                    prior_review=prior_review,
                )
                validation = validate_cad_source(design_output.source_code)
                if not validation.ok:
                    build_error = "; ".join(validation.errors)
                    prior_review = ReviewSummary(
                        decision=ReviewDecision.revise,
                        confidence=0.2,
                        key_findings=["Generated source failed the static safety/shape validator."],
                        suspect_or_missing_features=[],
                        suspect_dimensions_to_recheck=[],
                        revision_instructions=validation.errors,
                        summary="Source validation failed.",
                    )
                    continue

                source_path = revision_dir / "workspace" / "generated_model.py"
                source_path.write_text(design_output.source_code, encoding="utf-8")
                try:
                    bundle = self.cad_runtime.build_render_bundle(
                        model_path=source_path,
                        revision_dir=revision_dir,
                    )
                    break
                except Exception as exc:  # pragma: no cover - exercised in integration/UAT
                    build_error = str(exc)
                    self._write_progress(
                        run,
                        self._materialize_snapshot(run),
                        self._progress_event(
                            "build_failed",
                            "retrying",
                            "Build failed; requesting repair",
                            error=build_error,
                            build_attempt=build_attempt + 1,
                        ),
                    )
                    prior_review = ReviewSummary(
                        decision=ReviewDecision.revise,
                        confidence=0.1,
                        key_findings=["cad-cli build/render failed."],
                        suspect_or_missing_features=[],
                        suspect_dimensions_to_recheck=[],
                        revision_instructions=[build_error],
                        summary=(
                            "Repair the Python model source so cad-cli can build it successfully."
                        ),
                    )
                    continue

            if design_output is None or bundle is None:
                run.status = RunStatus.failed
                run.current_status_summary = "Run failed during CAD build"
                self._write_progress(
                    run,
                    self._materialize_snapshot(run),
                    self._progress_event(
                        "run_failed",
                        "error",
                        "Run failed during CAD build",
                        error=build_error or "unknown build failure",
                    ),
                )
                raise RuntimeError(build_error or "unable to produce buildable CAD source")

            revision.status = "persisted"
            self.store.write_json_file(revision_dir / "artifact-manifest.json", bundle.manifest)
            self.store.write_json_file(
                revision_dir / "inspect-summary.json",
                bundle.inspect_summary,
            )
            self.store.write_revision(run.run_name, revision)
            run.revisions.append(revision)
            run.artifact_references = {
                role: entry.path for role, entry in bundle.manifest.entries.items()
            }
            self._write_progress(
                run,
                self._materialize_snapshot(run),
                self._progress_event(
                    "revision_persisted",
                    "ok",
                    f"Revision {revision.revision_name} persisted",
                    revision_id=revision.revision_id,
                ),
            )

            final_review = await self._review_revision(
                run=run,
                bundle=bundle,
                revision_dir=revision_dir,
                model=profile.model,
                reasoning=profile.reasoning,
                context=context,
                reference_image=request.reference_image,
            )
            review_path = revision_dir / "review-summary.json"
            self.store.write_json_file(review_path, final_review)
            revision.review_summary_path = str(review_path)
            revision.status = "reviewed"
            self.store.write_revision(run.run_name, revision)
            run.review_outputs[revision.revision_id] = str(review_path)
            run.current_status_summary = final_review.summary
            self._write_progress(
                run,
                self._materialize_snapshot(run, review_path=str(review_path)),
                self._progress_event(
                    "review_completed",
                    "ok",
                    "Review completed",
                    decision=final_review.decision.value,
                    confidence=final_review.confidence,
                ),
            )

            if final_review.decision == ReviewDecision.accept:
                run.status = RunStatus.completed
                break

            prior_review = final_review
            self._write_progress(
                run,
                self._materialize_snapshot(run, review_path=str(review_path)),
                self._progress_event(
                    "revision_requested",
                    "ok",
                    "Review requested another revision",
                    revision_instructions=final_review.revision_instructions,
                ),
            )

        if run.status != RunStatus.completed:
            run.status = RunStatus.completed if final_review else RunStatus.failed

        trace_path = self.store.run_dir(run.run_name) / "execution-trace.json"
        self.store.write_json_file(trace_path, context.trace_events)
        final_message = await self._final_delivery_message(
            run=run,
            final_review=final_review,
            model=profile.model,
            reasoning=profile.reasoning,
            context=context,
        )
        run.current_status_summary = (
            "Run completed" if run.status == RunStatus.completed else "Run failed"
        )
        final_snapshot = self._materialize_snapshot(
            run,
            review_path=next(reversed(run.review_outputs.values())) if run.review_outputs else None,
        )
        self._write_progress(
            run,
            final_snapshot,
            self._progress_event(
                "run_completed" if run.status == RunStatus.completed else "run_failed",
                "ok" if run.status == RunStatus.completed else "error",
                "Run completed" if run.status == RunStatus.completed else "Run failed",
            ),
        )
        return HarnessOutcome(run=run, snapshot=final_snapshot, final_message=final_message)

    async def run(self, request: RunCreateRequest) -> HarnessOutcome:
        profile_name = request.profile or self.config.runtime.default_profile
        run = self.begin_run(request)
        return await self._execute_existing_run(request=request, run=run, profile_name=profile_name)

    async def continue_run(self, run_name: str, request: RunCreateRequest) -> HarnessOutcome:
        profile_name = request.profile or self.config.runtime.default_profile
        run = self.store.load_run(run_name)
        return await self._execute_existing_run(request=request, run=run, profile_name=profile_name)

    def run_sync(self, request: RunCreateRequest) -> HarnessOutcome:
        return asyncio.run(self.run(request))
