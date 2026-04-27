"""Eval batch runner (FLH-F-006, FLH-F-014, FLH-F-015, FLH-D-018)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from ..agents import Runner, build_judge
from ..config.profiles import HarnessConfig
from ..orchestrator import RunDriver
from ..orchestrator.run_driver import DriveRequest
from ..runtime.cad_cli import cad_compare
from ..schemas import DeterministicMetrics, JudgeOutput
from ..sdk_messages import build_single_user_multimodal_message
from .dataset import EvalCase, load_cases


def _batch_dir(config: HarnessConfig, batch_name: str) -> Path:
    out = config.evals_dir / batch_name
    out.mkdir(parents=True, exist_ok=True)
    return out


def _delivered_step(config: HarnessConfig, run_name: str, rev_name: str) -> Path:
    return config.runs_dir / run_name / "revisions" / rev_name / "model.step"


async def run_eval_batch(
    *,
    dataset_path: Path,
    config: HarnessConfig,
    profile: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    batch_name: str | None = None,
    max_revisions: int | None = None,
    role_model_overrides: dict[str, str] | None = None,
    role_reasoning_overrides: dict[str, str] | None = None,
) -> Path:
    cases = load_cases(dataset_path)
    batch_name = batch_name or datetime.utcnow().strftime("batch-%Y%m%d-%H%M%S")
    batch_dir = _batch_dir(config, batch_name)
    # Record "latest" pointer for easy reporting.
    (config.evals_dir / "latest.txt").write_text(batch_name)

    batch_summary: list[dict] = []
    base_eval_profile = config.profile(profile or "normal")
    role_profiles = config.resolve_role_profiles(
        base_eval_profile,
        global_model=model,
        global_reasoning=effort,
        role_model_overrides=role_model_overrides,
        role_reasoning_overrides=role_reasoning_overrides,
    )
    eval_profile = role_profiles["judge"]

    for case in cases:
        case_dir = batch_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "case.json").write_text(
            json.dumps(
                {
                    "case_id": case.case_id,
                    "prompt": case.prompt,
                    "spec": case.spec,
                    "tags": case.tags,
                },
                indent=2,
            )
        )

        driver = RunDriver(config)
        result = await driver.run(
            DriveRequest(
                prompt=case.prompt,
                profile_name=profile,
                model_override=model,
                reasoning_override=effort,
                reference_image=str(case.reference_image) if case.reference_image else None,
                max_revisions=max_revisions,
                role_model_overrides=role_model_overrides,
                role_reasoning_overrides=role_reasoning_overrides,
            )
        )
        (case_dir / "drive-result.json").write_text(json.dumps(result, indent=2))

        rec: dict = {
            "case_id": case.case_id,
            "run_name": result["run_name"],
            "status": result["status"],
            "delivered_revision": result["delivered_revision"],
            "metrics": None,
            "judge": None,
        }

        delivered = result.get("delivered_revision")
        if delivered and case.ground_truth_step.is_file():
            step = _delivered_step(config, result["run_name"], delivered)
            cmp = cad_compare(
                left_path=case.ground_truth_step,
                right_path=step,
                output_dir=case_dir / "compare",
                alignment="principal",
            )
            metrics = DeterministicMetrics(
                case_id=case.case_id,
                mode=cmp.metrics.mode,
                alignment=cmp.metrics.alignment,
                left_volume=cmp.metrics.left_volume,
                right_volume=cmp.metrics.right_volume,
                shared_volume=cmp.metrics.shared_volume,
                overlap_ratio=cmp.metrics.overlap_ratio,
                notes=cmp.metrics.notes,
            )
            metrics_path = case_dir / "deterministic-metrics.json"
            metrics_path.write_text(metrics.model_dump_json(indent=2))
            rec["metrics"] = metrics.model_dump()

            judge = await _judge_case(
                case=case,
                metrics=metrics,
                config=config,
                run_name=result["run_name"],
                delivered_revision=delivered,
                eval_profile=eval_profile,
            )
            judge_path = case_dir / "judge-output.json"
            judge_path.write_text(judge.model_dump_json(indent=2, by_alias=True))
            rec["judge"] = judge.model_dump(by_alias=True)

        batch_summary.append(rec)

    # Aggregate.
    summary_path = batch_dir / "batch-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "batch_name": batch_name,
                "dataset": str(dataset_path),
                "profile": profile or config.default_profile,
                "cases": batch_summary,
            },
            indent=2,
        )
    )
    return summary_path


async def _judge_case(
    *,
    case: EvalCase,
    metrics: DeterministicMetrics,
    config: HarnessConfig,
    run_name: str,
    delivered_revision: str,
    eval_profile,
) -> JudgeOutput:
    judge = build_judge(eval_profile)
    payload = {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "spec": case.spec,
        "deterministic_metrics": metrics.model_dump(),
        "review_focus": {
            "primary_modality": "visual",
            "feature_checklist": "Use flexible, high-signal criteria implied by case spec.",
        },
    }
    render_sheet = (
        config.runs_dir / run_name / "revisions" / delivered_revision / "render-sheet.png"
    )
    images = [render_sheet]
    if case.reference_image:
        images.append(case.reference_image)
    result = await Runner.run(
        judge,
        input=cast(
            Any,
            build_single_user_multimodal_message(
                lead_text="Judge this delivered CAD revision against ground truth.",
                payload=payload,
                image_paths=images,
            ),
        ),
    )
    return result.final_output
