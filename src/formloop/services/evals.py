"""Developer eval orchestration."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from agents import Runner

from ..agents.common import ExecutionTraceHooks, HarnessAgentContext
from ..agents.quality_specialist import build_quality_specialist_agent
from ..config import HarnessConfig, load_config
from ..models import (
    DeterministicMetricsOutput,
    EvalAggregateReport,
    EvalCase,
    EvalCaseResult,
    EvalPassStatus,
    RunCreateRequest,
)
from ..paths import dataset_root
from ..runtime.cad import CadCliRuntime
from .harness import HarnessOutcome, HarnessService


class EvalService:
    # Req: FLH-F-014, FLH-F-015, FLH-V-008
    def __init__(
        self,
        *,
        config: HarnessConfig | None = None,
        harness: HarnessService | None = None,
        cad_runtime: CadCliRuntime | None = None,
    ) -> None:
        self.config = config or load_config()
        self.harness = harness or HarnessService(config=self.config)
        self.cad_runtime = cad_runtime or CadCliRuntime()

    def _report_root(self) -> Path:
        root = self.config.run_root_path() / "eval-reports"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def load_dataset(self, dataset_path: str) -> list[EvalCase]:
        root = dataset_root() / dataset_path
        cases: list[EvalCase] = []
        for json_path in sorted(root.glob("*.json")):
            case = EvalCase.model_validate_json(json_path.read_text(encoding="utf-8"))
            if not Path(case.ground_truth_step).is_absolute():
                case.ground_truth_step = str((json_path.parent / case.ground_truth_step).resolve())
            if case.reference_image and not Path(case.reference_image).is_absolute():
                case.reference_image = str((json_path.parent / case.reference_image).resolve())
            cases.append(case)
        return cases

    async def _judge_case(
        self,
        *,
        case: EvalCase,
        outcome: HarnessOutcome,
        metrics: DeterministicMetricsOutput,
    ) -> tuple[Path, EvalPassStatus]:
        revision = outcome.run.revisions[-1]
        revision_dir = (
            self.config.run_root_path()
            / outcome.run.run_name
            / "revisions"
            / revision.revision_name
        )
        reviewer = build_quality_specialist_agent(
            model=outcome.run.effective_model,
            reasoning=outcome.run.effective_reasoning,
            mode="dev_eval",
        )
        context = HarnessAgentContext(run_id=outcome.run.run_id)
        result = await Runner.run(
            reviewer,
            cast(
                Any,
                [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    f"Evaluate case {case.case_id}\n"
                                    f"Prompt: {case.prompt}\n"
                                    f"Spec: {case.normalized_spec.model_dump_json()}\n"
                                    f"Metrics: {metrics.model_dump_json()}"
                                ),
                            }
                        ],
                    }
                ],
            ),
            context=context,
            hooks=ExecutionTraceHooks(),
        )
        judge = result.final_output
        judge_path = revision_dir / "judge-output.json"
        judge_path.write_text(judge.model_dump_json(indent=2), encoding="utf-8")
        return judge_path, judge.pass_status

    async def run_dataset(
        self,
        dataset_path: str,
        *,
        profile: str = "normal",
    ) -> EvalAggregateReport:
        cases = self.load_dataset(dataset_path)
        report_id = f"eval-report-{uuid4().hex[:8]}"
        report_dir = self._report_root() / report_id
        report_dir.mkdir(parents=True, exist_ok=True)

        case_results: list[EvalCaseResult] = []
        for case in cases:
            outcome = await self.harness.run(
                RunCreateRequest(
                    prompt=case.prompt,
                    profile=profile,
                    reference_image=case.reference_image,
                )
            )
            revision = outcome.run.revisions[-1]
            revision_dir = (
                self.config.run_root_path()
                / outcome.run.run_name
                / "revisions"
                / revision.revision_name
            )
            compare_dir = report_dir / case.case_id / "compare"
            compare_dir.mkdir(parents=True, exist_ok=True)
            compare = self.cad_runtime.compare(
                left=Path(revision_dir / "step.step"),
                right=Path(case.ground_truth_step),
                output_dir=compare_dir,
            )
            candidate_summary = self.cad_runtime.run_json(
                "inspect",
                "summary",
                str(revision_dir / "step.step"),
                "--format",
                "json",
            )
            truth_summary = self.cad_runtime.run_json(
                "inspect",
                "summary",
                str(case.ground_truth_step),
                "--format",
                "json",
            )
            overlap_ratio = compare["metrics"].get("overlap_ratio") or 0.0
            threshold = float(case.tolerances.get("min_overlap_ratio", 0.95))
            metrics = DeterministicMetricsOutput(
                case_id=case.case_id,
                run_id=outcome.run.run_id,
                revision_id=revision.revision_id,
                compare_metrics=compare["metrics"],
                candidate_summary=candidate_summary["data"],
                ground_truth_summary=truth_summary["data"],
                pass_thresholds={"min_overlap_ratio": threshold},
                pass_status=(
                    EvalPassStatus.pass_ if overlap_ratio >= threshold else EvalPassStatus.fail
                ),
            )
            metrics_path = report_dir / case.case_id / "deterministic-metrics-output.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(metrics.model_dump_json(indent=2), encoding="utf-8")
            judge_path, judge_status = await self._judge_case(
                case=case,
                outcome=outcome,
                metrics=metrics,
            )
            pass_status = (
                EvalPassStatus.pass_
                if (
                    metrics.pass_status == EvalPassStatus.pass_
                    and judge_status != EvalPassStatus.fail
                )
                else EvalPassStatus.fail
            )
            case_results.append(
                EvalCaseResult(
                    case_id=case.case_id,
                    run_id=outcome.run.run_id,
                    revision_id=revision.revision_id,
                    metrics_path=str(metrics_path),
                    judge_output_path=str(judge_path),
                    pass_status=pass_status,
                    summary=f"overlap_ratio={overlap_ratio:.4f}, threshold={threshold:.4f}",
                )
            )

        passed = sum(result.pass_status == EvalPassStatus.pass_ for result in case_results)
        failed = sum(result.pass_status == EvalPassStatus.fail for result in case_results)
        warnings = sum(result.pass_status == EvalPassStatus.warning for result in case_results)
        report = EvalAggregateReport(
            report_id=report_id,
            dataset_path=dataset_path,
            total_cases=len(case_results),
            passed_cases=passed,
            failed_cases=failed,
            warning_cases=warnings,
            case_results=case_results,
        )
        (report_dir / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return report

    def run_dataset_sync(
        self,
        dataset_path: str,
        *,
        profile: str = "normal",
    ) -> EvalAggregateReport:
        return asyncio.run(self.run_dataset(dataset_path, profile=profile))

    def load_latest_report(self) -> EvalAggregateReport:
        candidates = sorted(
            self._report_root().glob("*/report.json"),
            key=lambda path: path.stat().st_mtime,
        )
        if not candidates:
            raise FileNotFoundError("No eval reports found")
        return EvalAggregateReport.model_validate_json(candidates[-1].read_text(encoding="utf-8"))
