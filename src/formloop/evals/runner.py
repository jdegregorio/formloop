"""Eval batch runner (FLH-F-006, FLH-F-014, FLH-F-015, FLH-D-018)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..agents import (
    Runner,
    build_multimodal_user_message,
    build_quality_specialist_judge,
)
from ..config.profiles import HarnessConfig
from ..orchestrator import RunDriver
from ..orchestrator.run_driver import DriveRequest
from ..runtime.cad_cli import cad_compare
from ..schemas import DeterministicMetrics, JudgeOutput
from ..store.layout import RunLayout
from .dataset import EvalCase, load_cases


def _batch_dir(config: HarnessConfig, batch_name: str) -> Path:
    out = config.evals_dir / batch_name
    out.mkdir(parents=True, exist_ok=True)
    return out


def _delivered_step(config: HarnessConfig, run_name: str, rev_name: str) -> Path:
    return config.runs_dir / run_name / "revisions" / rev_name / "step.step"


def _delivered_revision_layout(config: HarnessConfig, run_name: str, rev_name: str):
    return RunLayout(runs_root=config.runs_dir, run_name=run_name).revision(rev_name)


_JUDGE_VIEW_ORDER = ("iso", "front", "top", "right", "back", "left", "bottom")


def _judge_image_paths(
    *,
    reference_image: Path | None,
    render_sheet: Path,
    views_dir: Path,
) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    if reference_image is not None:
        pairs.append(("REFERENCE IMAGE:", reference_image))
    pairs.append(("RENDER SHEET (7-view composite):", render_sheet))
    for name in _JUDGE_VIEW_ORDER:
        pairs.append((f"{name.upper()} VIEW:", views_dir / f"{name}.png"))
    return pairs


async def run_eval_batch(
    *,
    dataset_path: Path,
    config: HarnessConfig,
    profile: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    batch_name: str | None = None,
    max_revisions: int | None = None,
) -> Path:
    cases = load_cases(dataset_path)
    batch_name = batch_name or datetime.utcnow().strftime("batch-%Y%m%d-%H%M%S")
    batch_dir = _batch_dir(config, batch_name)
    # Record "latest" pointer for easy reporting.
    (config.evals_dir / "latest.txt").write_text(batch_name)

    batch_summary: list[dict] = []
    eval_profile = config.profile(profile or "normal")

    for case in cases:
        case_dir = batch_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "case.json").write_text(
            json.dumps(
                {
                    "case_id": case.case_id,
                    "prompt": case.prompt,
                    "spec": case.spec,
                    "tolerances": case.tolerances,
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
                reference_image=str(case.reference_image)
                if case.reference_image
                else None,
                max_revisions=max_revisions,
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

            rev_layout = _delivered_revision_layout(
                config, result["run_name"], delivered
            )
            judge = await _judge_case(
                case=case,
                metrics=metrics,
                eval_profile=eval_profile,
                render_sheet=rev_layout.render_sheet,
                views_dir=rev_layout.views_dir,
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
    eval_profile,
    render_sheet: Path,
    views_dir: Path,
) -> JudgeOutput:
    judge = build_quality_specialist_judge(eval_profile)
    payload = {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "spec": case.spec,
        "deterministic_metrics": metrics.model_dump(),
    }
    image_paths = _judge_image_paths(
        reference_image=case.reference_image,
        render_sheet=render_sheet,
        views_dir=views_dir,
    )
    judge_input = build_multimodal_user_message(
        text=(
            "Judge this delivered CAD revision against ground truth. Build the "
            "feature_checklist before scoring, and use the attached render sheet "
            "and view PNGs (and the reference image, if attached) as primary "
            "visual evidence alongside the deterministic metrics.\n\n"
            + json.dumps(payload, indent=2, default=str)
        ),
        image_paths=image_paths,
    )
    result = await Runner.run(judge, input=judge_input)
    return result.final_output
