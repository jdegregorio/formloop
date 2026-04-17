from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Iterable

from formloop.agents.backends import HeuristicBackend, LLMBackend, OpenAIAgentsBackend
from formloop.agents.contracts import (
    DesignerOutput,
    EvalJudgeOutput,
    EvalJudgePlan,
    ManagerAssessment,
    ResearchOutput,
    ReviewOutput,
    ReviewPlan,
)
from formloop.agents.skills import load_builtin_skill_texts
from formloop.config import HarnessConfig, RunProfile, env_snapshot, load_config, required_env_vars
from formloop.datasets import load_eval_cases
from formloop.models import (
    ArtifactRecord,
    AssumptionRecord,
    ClarificationEvent,
    DesignRequest,
    EffectiveRuntime,
    EvalBatchResult,
    EvalCaseResult,
    ResearchFinding,
    RevisionRecord,
    RunRecord,
    SubagentCallRecord,
    TraceEvent,
)
from formloop.runtime.cad import CadRuntime
from formloop.storage.files import FileRunStore
from formloop.types import ArtifactKind, ReviewDecision, RunStatus, TraceKind


def create_service(project_root: Path | None = None) -> "HarnessService":
    config = load_config(project_root)
    backend_name = os.getenv("FORMLOOP_LLM_BACKEND", config.app.llm_backend)
    cad_command = os.getenv("FORMLOOP_CAD_COMMAND", config.app.cad_command)
    backend: LLMBackend
    if backend_name == "heuristic":
        backend = HeuristicBackend()
    else:
        backend = OpenAIAgentsBackend()
    run_store = FileRunStore(config.run_store_path)
    cad_runtime = CadRuntime(cad_command=cad_command, cwd=config.project_root)
    skill_texts = load_builtin_skill_texts(config.project_root / config.skills.builtin_dir)
    return HarnessService(config, run_store, cad_runtime, backend, skill_texts)


class HarnessService:
    def __init__(
        self,
        config: HarnessConfig,
        store: FileRunStore,
        cad_runtime: CadRuntime,
        llm_backend: LLMBackend,
        skill_texts: dict[str, str],
    ) -> None:
        self.config = config
        self.store = store
        self.cad_runtime = cad_runtime
        self.llm_backend = llm_backend
        self.skill_texts = skill_texts

    def doctor(self, profiles: list[str] | None = None) -> dict:
        selected_profiles = profiles or [self.config.app.default_profile]
        missing_profiles = [name for name in selected_profiles if name not in self.config.profiles]
        env_vars = required_env_vars(self.config, selected_profiles)
        env_state = env_snapshot(env_vars)
        provider_checks = {}
        for name in selected_profiles:
            if name not in self.config.profiles:
                continue
            profile = self.config.profile(name)
            provider_checks[name] = {
                "provider": profile.provider.value,
                "model": profile.model,
                "resolvable": bool(profile.model),
            }
        issues = []
        if missing_profiles:
            issues.append(f"Unknown profiles: {', '.join(missing_profiles)}")
        if not self.cad_runtime.check_command():
            issues.append(f"cad command not found: {self.cad_runtime.cad_command}")
        for name, present in env_state.items():
            if not present:
                issues.append(f"Missing required environment variable: {name}")
        return {
            "ok": not issues,
            "profiles": selected_profiles,
            "env": env_state,
            "provider_checks": provider_checks,
            "cad_command": self.cad_runtime.cad_command,
            "llm_backend": self.llm_backend.backend_name,
            "issues": issues,
        }

    def execute_run(self, request: DesignRequest) -> RunRecord:
        profile_name = request.profile or self.config.app.default_profile
        profile = self.config.profile(profile_name)
        runtime = EffectiveRuntime(
            profile=profile_name,
            provider=profile.provider.value,
            model=profile.model,
            thinking=profile.thinking.value,
            backend=self.llm_backend.backend_name,
        )
        record = RunRecord(
            prompt=request.prompt,
            reference_image=request.reference_image,
            effective_runtime=runtime,
            mode=request.run_mode,
        )
        self.store.create_run(record)
        self._event(record, TraceKind.PROGRESS, "Run created.")
        record.status = RunStatus.RUNNING
        self.store.save_run(record)

        if request.reference_image:
            self._persist_reference_image(record, Path(request.reference_image.path))

        manager = self._manager_assessment(record, request.prompt, profile)
        record.current_spec = manager.normalized_spec
        if manager.assumptions:
            for text in manager.assumptions:
                assumption = AssumptionRecord(text=text, rationale="Manager first-pass default")
                record.assumptions.append(assumption)
                self._event(record, TraceKind.ASSUMPTION, text, {"rationale": assumption.rationale})

        if manager.needs_clarification:
            clarification = ClarificationEvent(
                reason=manager.clarification_reason or "critical gaps detected",
                questions=manager.clarification_questions,
                blocking=True,
            )
            record.clarifications.append(clarification)
            record.status = RunStatus.NEEDS_CLARIFICATION
            self._event(
                record,
                TraceKind.CLARIFICATION,
                clarification.reason,
                {"questions": clarification.questions},
            )
            self.store.save_run(record)
            return record

        research = self._run_research(manager.research_topics, record, profile)
        revision_feedback: list[str] = []
        max_revisions = self.config.runtime.max_review_revisions

        for revision_index in range(max_revisions + 1):
            revision = self._run_revision(
                record=record,
                revision_index=revision_index,
                profile=profile,
                research=research,
                revision_feedback=revision_feedback,
            )
            record.revisions.append(revision)
            record.latest_review_summary = revision.review_summary
            preserved_artifacts = [artifact for artifact in record.final_artifacts if artifact.kind == ArtifactKind.REFERENCE_IMAGE]
            record.final_artifacts = preserved_artifacts + revision.artifacts
            if revision.review_summary and revision.review_summary.decision == ReviewDecision.PASS:
                record.status = RunStatus.SUCCEEDED
                break
            revision_feedback = revision.review_summary.revision_instructions if revision.review_summary else []
        else:
            record.status = RunStatus.FAILED
            record.error_message = "Exceeded maximum review revisions."

        if record.status == RunStatus.PENDING:
            record.status = RunStatus.FAILED
            record.error_message = "Run ended without terminal status."
        record.touch()
        self.store.save_run(record)
        return record

    def execute_eval(self, dataset_name: str, profile_name: str | None = None) -> EvalBatchResult:
        profile_name = profile_name or "eval"
        profile = self.config.profile(profile_name)
        dataset_root = self.config.project_root / self.config.datasets.root
        cases = load_eval_cases(dataset_root, dataset_name)
        results: list[EvalCaseResult] = []
        failures: list[str] = []

        eval_dir = self.store.evals_dir / dataset_name
        eval_dir.mkdir(parents=True, exist_ok=True)

        for case in cases:
            run = self.execute_run(
                DesignRequest(
                    prompt=case.prompt,
                    profile=profile_name,
                    reference_image=None,
                )
            )
            if run.status != RunStatus.SUCCEEDED or not run.final_artifacts:
                failures.append(case.case_id)
                continue
            candidate_step = next(artifact for artifact in run.final_artifacts if artifact.kind == ArtifactKind.STEP)
            compare_result, compare_call = self.cad_runtime.compare(
                self._artifact_full_path(run, candidate_step.path),
                Path(case.ground_truth_step),
            )
            judge_plan = self._llm_call(
                role_name="Eval Specialist plan",
                purpose="plan eval judge inspections",
                instructions=self._skill_prompt(["eval_execution"]),
                prompt=f"Dataset case: {case.case_id}\nPrompt: {case.prompt}\nMetrics: {json.dumps(compare_result.metrics)}",
                output_type=EvalJudgePlan,
                profile=profile,
                record=run,
            )
            inspect_payload = {}
            if judge_plan.requested_measurements:
                inspect_result, inspect_call = self.cad_runtime.inspect(
                    self._artifact_full_path(run, candidate_step.path),
                    judge_plan.requested_measurements,
                )
                inspect_payload = inspect_result.measurements
                self._append_tool_to_run(run, inspect_call)
            judge_output = self._llm_call(
                role_name="Eval Specialist",
                purpose="produce eval judge result",
                instructions=self._skill_prompt(["eval_execution"]),
                prompt=(
                    f"Dataset case: {case.case_id}\nPrompt: {case.prompt}\n"
                    f"Deterministic metrics: {json.dumps(compare_result.metrics)}\n"
                    f"Inspections: {json.dumps(inspect_payload)}"
                ),
                output_type=EvalJudgeOutput,
                profile=profile,
                record=run,
            )
            self._append_tool_to_run(run, compare_call)
            metrics_path = eval_dir / f"{case.case_id}.metrics.json"
            judge_path = eval_dir / f"{case.case_id}.judge.json"
            metrics_path.write_text(json.dumps(compare_result.metrics, indent=2), encoding="utf-8")
            judge_path.write_text(judge_output.model_dump_json(indent=2), encoding="utf-8")
            score_status = "pass" if judge_output.acceptable else "fail"
            if score_status == "fail":
                failures.append(case.case_id)
            results.append(
                EvalCaseResult(
                    case_id=case.case_id,
                    run_id=run.run_id,
                    deterministic_metrics=compare_result.metrics,
                    judge_outputs=judge_output.model_dump(mode="json"),
                    score_status=score_status,
                    summary_markdown=(
                        f"# {case.case_id}\n\n"
                        f"- Score status: {score_status}\n"
                        f"- Notes: {'; '.join(judge_output.notes)}\n"
                    ),
                    artifact_bundle=run.final_artifacts
                    + [
                        ArtifactRecord(
                            kind=ArtifactKind.METRICS,
                            path=self._path_ref(metrics_path),
                            revision=0,
                            label=f"{case.case_id} metrics",
                        ),
                        ArtifactRecord(
                            kind=ArtifactKind.JUDGE_OUTPUT,
                            path=self._path_ref(judge_path),
                            revision=0,
                            label=f"{case.case_id} judge output",
                        ),
                    ],
                )
            )

        aggregate = {
            "case_count": len(cases),
            "passed": sum(1 for item in results if item.score_status == "pass"),
            "failed": len(failures),
        }
        report_path = eval_dir / "latest.md"
        report_path.write_text(
            "# Eval Summary\n\n"
            + f"- Dataset: {dataset_name}\n"
            + f"- Passed: {aggregate['passed']}\n"
            + f"- Failed: {aggregate['failed']}\n",
            encoding="utf-8",
        )
        batch = EvalBatchResult(
            dataset=dataset_name,
            case_results=results,
            aggregate_metrics=aggregate,
            failure_shortlist=failures,
            report_path=self._path_ref(report_path),
        )
        return batch

    def latest_eval_report(self, dataset_name: str) -> Path:
        return self.store.evals_dir / dataset_name / "latest.md"

    def load_run(self, run_id: str) -> RunRecord:
        return self.store.load_run(run_id)

    def _manager_assessment(self, record: RunRecord, prompt: str, profile: RunProfile) -> ManagerAssessment:
        return self._llm_call(
            role_name="Manager",
            purpose="assess request and normalize spec",
            instructions=(
                "You are the Formloop manager. Attempt a first CAD iteration by default. "
                "Ask clarifying questions only when critical gaps block a credible initial model. "
                "A critical gap means missing core function, a mandatory interface, or must-hit dimensions/tolerances "
                "without which the first model would likely be unusable. "
                "Do not block on normal engineering defaults. If the user requests named standards, threaded holes, "
                "fasteners, chamfers, gears, escapements, or other familiar mechanical conventions, make reasonable "
                "industry-standard assumptions, record them, and let the CAD Designer and Researcher carry those "
                "assumptions forward. "
                "For example: if an M3 threaded hole is requested without thread-depth detail, assume a standard "
                "through-tapped M3x0.5 hole unless the part geometry makes that impossible. If a 0.5 mm chamfer is "
                "requested on a bracket edge, assume it applies to the external perimeter edges unless the user says "
                "otherwise. If a rectangular plate or bracket has a centered multi-hole pattern with spacing given but "
                "no axis specified, assume the spacing runs along the longest major in-plane dimension unless the user "
                "states a different orientation, and record that assumption rather than blocking. "
                "Return structured output only."
            ),
            prompt=prompt,
            output_type=ManagerAssessment,
            profile=profile,
            record=record,
        )

    def _run_research(self, topics: Iterable[str], record: RunRecord, profile: RunProfile) -> list[ResearchFinding]:
        findings: list[ResearchFinding] = []
        for topic in topics:
            output = self._llm_call(
                role_name="Design Researcher",
                purpose="research named standards or conventions",
                instructions=self._skill_prompt(["design_research"]),
                prompt=topic,
                output_type=ResearchOutput,
                profile=profile,
                record=record,
            )
            finding = ResearchFinding(topic=output.topic, findings=output.findings, citations=output.citations)
            findings.append(finding)
            self._event(record, TraceKind.RESEARCH, topic, {"findings": output.findings, "citations": output.citations})
        return findings

    def _run_revision(
        self,
        *,
        record: RunRecord,
        revision_index: int,
        profile: RunProfile,
        research: list[ResearchFinding],
        revision_feedback: list[str],
    ) -> RevisionRecord:
        revision_dir = self.store.run_dir(record.run_id) / "revisions" / str(revision_index)
        revision_dir.mkdir(parents=True, exist_ok=True)
        designer_prompt = (
            f"Prompt: {record.prompt}\n"
            f"Spec: {record.current_spec.model_dump_json(indent=2)}\n"
            f"Assumptions: {[item.text for item in record.assumptions]}\n"
            f"Research: {[item.model_dump(mode='json') for item in research]}\n"
            f"Revision instructions: {revision_feedback}\n"
        )
        designer_output = self._llm_call(
            role_name="CAD Designer",
            purpose="produce model source",
            instructions=self._skill_prompt(["build123d_modeling"]),
            prompt=designer_prompt,
            output_type=DesignerOutput,
            profile=profile,
            record=record,
        )
        model_source_path = revision_dir / "model.py"
        model_source_path.write_text(designer_output.model_source, encoding="utf-8")
        build_result, build_call = self.cad_runtime.build(model_source_path, revision_dir / "build")
        render_result, render_call = self.cad_runtime.render(Path(build_result.glb_path), revision_dir / "render")
        build_metadata = self._read_json_file(Path(build_result.metadata_path))
        render_metadata = self._read_json_file(Path(render_result.metadata_path)) if render_result.metadata_path else None

        artifacts = [
            ArtifactRecord(
                kind=ArtifactKind.MODEL_SOURCE,
                path=self._run_artifact_ref(record, model_source_path),
                revision=revision_index,
                label=f"revision {revision_index} model source",
            ),
            ArtifactRecord(
                kind=ArtifactKind.STEP,
                path=self._run_artifact_ref(record, Path(build_result.step_path)),
                revision=revision_index,
                label=f"revision {revision_index} step",
            ),
            ArtifactRecord(
                kind=ArtifactKind.GLB,
                path=self._run_artifact_ref(record, Path(build_result.glb_path)),
                revision=revision_index,
                label=f"revision {revision_index} glb",
            ),
            ArtifactRecord(
                kind=ArtifactKind.RENDER_SHEET,
                path=self._run_artifact_ref(record, Path(render_result.render_sheet_path)),
                revision=revision_index,
                label=f"revision {revision_index} render sheet",
            ),
        ]

        review_images = [render_result.render_sheet_path]
        reference_image_path = None
        if record.reference_image:
            reference_image_path = self._reference_image_path(record)
            if reference_image_path:
                review_images.append(str(reference_image_path))

        review_plan = self._llm_call(
            role_name="Review Specialist plan",
            purpose="plan review inspections",
            instructions=self._skill_prompt(["internal_design_review"]),
            prompt=(
                f"Prompt: {record.prompt}\n"
                f"Spec: {record.current_spec.model_dump_json(indent=2)}\n"
                f"Build metadata: {json.dumps(build_metadata)}\n"
                f"Render metadata: {json.dumps(render_metadata)}\n"
                f"Reference image present: {bool(record.reference_image)}\n"
            ),
            output_type=ReviewPlan,
            profile=profile,
            record=record,
            image_paths=review_images,
        )
        inspect_result, inspect_call = self.cad_runtime.inspect(Path(build_result.step_path), review_plan.requested_measurements)
        review_output = self._llm_call(
            role_name="Review Specialist",
            purpose="produce review summary",
            instructions=self._skill_prompt(["internal_design_review"]),
            prompt=(
                f"Prompt: {record.prompt}\n"
                f"Spec: {record.current_spec.model_dump_json(indent=2)}\n"
                f"Build metadata: {json.dumps(build_metadata)}\n"
                f"Render metadata: {json.dumps(render_metadata)}\n"
                f"Measurements: {json.dumps(inspect_result.measurements)}\n"
                f"Feature checks: {review_plan.requested_feature_checks}\n"
                f"Reference image present: {bool(record.reference_image)}\n"
            ),
            output_type=ReviewOutput,
            profile=profile,
            record=record,
            image_paths=review_images,
        )
        review_summary_path = revision_dir / "review_summary.json"
        review_summary_path.write_text(review_output.summary.model_dump_json(indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRecord(
                kind=ArtifactKind.REVIEW_SUMMARY,
                path=self._run_artifact_ref(record, review_summary_path),
                revision=revision_index,
                label=f"revision {revision_index} review summary",
            )
        )

        revision = RevisionRecord(
            revision_index=revision_index,
            model_source=designer_output.model_source,
            spec=record.current_spec,
            artifacts=artifacts,
            review_summary=review_output.summary,
            research=research,
        )
        revision.tool_calls.extend([build_call, render_call, inspect_call])
        revision.trace_events.extend(record.trace_events[-3:])
        self._event(record, TraceKind.REVIEW, f"Revision {revision_index} review decision: {review_output.summary.decision.value}")
        self._append_tool_to_run(record, build_call)
        self._append_tool_to_run(record, render_call)
        self._append_tool_to_run(record, inspect_call)
        self.store.save_run(record)
        return revision

    def _append_tool_to_run(self, record: RunRecord, tool_call) -> None:
        record.tool_calls.append(tool_call)
        self._event(
            record,
            TraceKind.TOOL_CALL,
            tool_call.tool,
            {"command": tool_call.command, "returncode": tool_call.returncode},
        )

    def _persist_reference_image(self, record: RunRecord, source: Path) -> None:
        if not source.exists():
            return
        target = self.store.run_dir(record.run_id) / "reference" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        record.final_artifacts.append(
            ArtifactRecord(
                kind=ArtifactKind.REFERENCE_IMAGE,
                path=self._run_artifact_ref(record, target),
                revision=0,
                label="reference image",
            )
        )

    def _read_json_file(self, path: Path | None) -> dict | None:
        if path is None or not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _event(self, record: RunRecord, kind: TraceKind, message: str, payload: dict | None = None) -> TraceEvent:
        event = TraceEvent(kind=kind, message=message, payload=payload or {})
        record.trace_events.append(event)
        record.touch()
        self.store.append_event(record.run_id, event)
        self.store.save_run(record)
        return event

    def _llm_call(
        self,
        *,
        role_name: str,
        purpose: str,
        instructions: str,
        prompt: str,
        output_type,
        profile: RunProfile,
        record: RunRecord,
        image_paths: list[str] | None = None,
    ):
        prompt_excerpt = prompt[:200]
        self._event(record, TraceKind.SUBAGENT_CALL, f"{role_name}: {purpose}", {"prompt_excerpt": prompt_excerpt})
        record.subagent_calls.append(
            SubagentCallRecord(agent_name=role_name, purpose=purpose, prompt_excerpt=prompt_excerpt)
        )
        return self.llm_backend.structured_completion(
            role_name=role_name,
            instructions=instructions,
            prompt=prompt,
            output_type=output_type,
            profile=profile,
            trace_metadata={"run_id": record.run_id, "purpose": purpose},
            image_paths=image_paths,
        )

    def _skill_prompt(self, skill_names: list[str]) -> str:
        blocks = []
        for name in skill_names:
            text = self.skill_texts.get(name)
            if text:
                blocks.append(text)
        return "\n\n".join(blocks) if blocks else "Return concise structured output."

    def _path_ref(self, path: Path) -> str:
        path = path.resolve()
        try:
            return str(path.relative_to(self.config.project_root))
        except ValueError:
            return str(path)

    def _run_artifact_ref(self, record: RunRecord, path: Path) -> str:
        path = path.resolve()
        try:
            return str(path.relative_to(self.store.run_dir(record.run_id)))
        except ValueError:
            return self._path_ref(path)

    def _artifact_full_path(self, record: RunRecord, artifact_path: str) -> Path:
        path = Path(artifact_path)
        if path.is_absolute():
            return path
        run_local = self.store.run_dir(record.run_id) / artifact_path
        if run_local.exists():
            return run_local
        return self.config.project_root / artifact_path

    def _reference_image_path(self, record: RunRecord) -> Path | None:
        for artifact in record.final_artifacts:
            if artifact.kind == ArtifactKind.REFERENCE_IMAGE:
                return self._artifact_full_path(record, artifact.path)
        return None
