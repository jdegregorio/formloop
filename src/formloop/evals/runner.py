"""Eval batch runner (FLH-F-006, FLH-F-014, FLH-F-015, FLH-D-018)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from ..agents import Runner, build_judge
from ..config.profiles import HarnessConfig, Profile
from ..orchestrator import RunDriver
from ..orchestrator.run_driver import DriveRequest
from ..runtime.cad_cli import cad_compare
from ..schemas import DeterministicMetrics, JudgeOutput
from ..sdk_messages import build_single_user_multimodal_message
from .dataset import EvalCase, load_cases, resolve_dataset_path

DEFAULT_WORKERS = 5
SERIALIZATION_REASON = (
    "parallel case execution is temporarily disabled because run logger isolation "
    "is not process-safe yet"
)
STAGE_RUN_STARTED = "run_started"
STAGE_REVISION_DELIVERED = "revision_delivered"
STAGE_BUILD_ARTIFACTS_AVAILABLE = "build_artifacts_available"
STAGE_COMPARE_COMPLETED = "compare_completed"
STAGE_JUDGE_COMPLETED = "judge_completed"
OUTCOME_STAGES = (
    STAGE_RUN_STARTED,
    STAGE_REVISION_DELIVERED,
    STAGE_BUILD_ARTIFACTS_AVAILABLE,
    STAGE_COMPARE_COMPLETED,
    STAGE_JUDGE_COMPLETED,
)


def _batch_dir(config: HarnessConfig, batch_name: str) -> Path:
    out = config.evals_dir / batch_name
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"eval batch directory already exists and is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    return out


def _delivered_revision_dir(config: HarnessConfig, run_name: str, rev_name: str) -> Path:
    return config.runs_dir / run_name / "revisions" / rev_name


def _delivered_step(config: HarnessConfig, run_name: str, rev_name: str) -> Path:
    return _delivered_revision_dir(config, run_name, rev_name) / "model.step"


def _revision_artifacts_available(config: HarnessConfig, run_name: str, rev_name: str) -> bool:
    rev_dir = _delivered_revision_dir(config, run_name, rev_name)
    required = ("model.step", "model.glb", "render-sheet.png")
    return all((rev_dir / name).is_file() for name in required)


def _stage_record() -> dict[str, bool]:
    return {stage: False for stage in OUTCOME_STAGES}


def _case_record(
    *,
    case: EvalCase,
    reference_images_enabled: bool,
) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "run_name": None,
        "status": "not_started",
        "delivered_revision": None,
        "metrics": None,
        "judge": None,
        "stages": _stage_record(),
        "reference_image_available": case.reference_image is not None,
        "reference_image_used": bool(reference_images_enabled and case.reference_image),
        "error": None,
    }


def _write_json(path: Path, payload: Mapping[str, Any] | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def _write_case_error(
    case_dir: Path,
    *,
    stage: str,
    exc: BaseException | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    error = {
        "stage": stage,
        "error_type": type(exc).__name__ if exc is not None else "EvalCaseIncomplete",
        "message": str(exc) if exc is not None else (message or "eval case incomplete"),
    }
    _write_json(case_dir / "case-error.json", error)
    return error


def _rate(passed: int, total: int) -> dict[str, int | float | None]:
    return {
        "passed": passed,
        "total": total,
        "rate": round(passed / total, 6) if total else None,
    }


def _aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(cases)
    judged = [case for case in cases if (case.get("stages") or {}).get(STAGE_JUDGE_COMPLETED)]
    compare_and_judged = [
        case
        for case in cases
        if (case.get("stages") or {}).get(STAGE_COMPARE_COMPLETED)
        and (case.get("stages") or {}).get(STAGE_JUDGE_COMPLETED)
    ]

    judge_passes = 0
    for case in judged:
        judge = case.get("judge") or {}
        if judge.get("pass") is True:
            judge_passes += 1

    agreements = 0
    for case in compare_and_judged:
        metrics = case.get("metrics") or {}
        judge = case.get("judge") or {}
        overlap = metrics.get("overlap_ratio")
        judge_pass = judge.get("pass") if "pass" in judge else None
        if overlap is not None and judge_pass is not None and (overlap >= 0.95) == bool(judge_pass):
            agreements += 1

    return {
        "total_cases": total,
        "run_success": _rate(sum(1 for case in cases if case.get("status") == "succeeded"), total),
        "revision_delivered": _rate(
            sum(1 for case in cases if (case.get("stages") or {}).get(STAGE_REVISION_DELIVERED)),
            total,
        ),
        "build_artifacts_available": _rate(
            sum(
                1
                for case in cases
                if (case.get("stages") or {}).get(STAGE_BUILD_ARTIFACTS_AVAILABLE)
            ),
            total,
        ),
        "compare_completed": _rate(
            sum(1 for case in cases if (case.get("stages") or {}).get(STAGE_COMPARE_COMPLETED)),
            total,
        ),
        "judge_completed": _rate(
            sum(1 for case in cases if (case.get("stages") or {}).get(STAGE_JUDGE_COMPLETED)),
            total,
        ),
        "judge_pass": _rate(judge_passes, len(judged)),
        "deterministic_judge_agreement": _rate(agreements, len(compare_and_judged)),
    }


def _role_runtime_payload(role_profiles: dict[str, Profile]) -> dict[str, dict[str, str]]:
    return {
        role: {"model": role_profile.model, "reasoning": role_profile.reasoning}
        for role, role_profile in role_profiles.items()
    }


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
    workers: int = DEFAULT_WORKERS,
    reference_images_enabled: bool = True,
) -> Path:
    dataset_path = resolve_dataset_path(dataset_path)
    cases = load_cases(dataset_path)
    requested_workers = max(1, workers)
    workers = 1
    batch_name = batch_name or datetime.utcnow().strftime("batch-%Y%m%d-%H%M%S")
    batch_dir = _batch_dir(config, batch_name)
    # Record "latest" pointer for easy reporting.
    (config.evals_dir / "latest.txt").write_text(batch_name)

    base_eval_profile = config.profile(profile or "normal")
    role_profiles = config.resolve_role_profiles(
        base_eval_profile,
        global_model=model,
        global_reasoning=effort,
        role_model_overrides=role_model_overrides,
        role_reasoning_overrides=role_reasoning_overrides,
    )
    effective_runtime = {
        "profile": base_eval_profile.name,
        "model": model or base_eval_profile.model,
        "reasoning": effort or base_eval_profile.reasoning,
        "roles": _role_runtime_payload(role_profiles),
    }

    semaphore = asyncio.Semaphore(workers)

    async def run_one(index: int, case: EvalCase) -> tuple[int, dict[str, Any]]:
        async with semaphore:
            case_dir = batch_dir / case.case_id
            try:
                rec = await asyncio.to_thread(
                    _run_case_in_thread,
                    case=case,
                    case_dir=case_dir,
                    config=config,
                    profile=profile,
                    model=model,
                    effort=effort,
                    max_revisions=max_revisions,
                    role_model_overrides=role_model_overrides,
                    role_reasoning_overrides=role_reasoning_overrides,
                    eval_profile=role_profiles["judge"],
                    reference_images_enabled=reference_images_enabled,
                )
            except Exception as exc:  # noqa: BLE001 -- batch should keep running.
                rec = _case_record(case=case, reference_images_enabled=reference_images_enabled)
                rec["status"] = "error"
                rec["error"] = _write_case_error(case_dir, stage=STAGE_RUN_STARTED, exc=exc)
            return index, rec

    indexed_results = await asyncio.gather(
        *(run_one(index, case) for index, case in enumerate(cases))
    )
    batch_summary = [rec for _, rec in sorted(indexed_results, key=lambda item: item[0])]

    summary_path = batch_dir / "batch-summary.json"
    _write_json(
        summary_path,
        {
            "batch_name": batch_name,
            "dataset": str(dataset_path),
            "requested_workers": requested_workers,
            "workers": workers,
            "worker_warning": SERIALIZATION_REASON if requested_workers > workers else None,
            "reference_images_enabled": reference_images_enabled,
            "effective_runtime": effective_runtime,
            "aggregate": _aggregate(batch_summary),
            "cases": batch_summary,
        },
    )
    return summary_path


def _run_case_in_thread(
    *,
    case: EvalCase,
    case_dir: Path,
    config: HarnessConfig,
    profile: str | None,
    model: str | None,
    effort: str | None,
    max_revisions: int | None,
    role_model_overrides: dict[str, str] | None,
    role_reasoning_overrides: dict[str, str] | None,
    eval_profile: Profile,
    reference_images_enabled: bool,
) -> dict[str, Any]:
    return asyncio.run(
        _run_case(
            case=case,
            case_dir=case_dir,
            config=config,
            profile=profile,
            model=model,
            effort=effort,
            max_revisions=max_revisions,
            role_model_overrides=role_model_overrides,
            role_reasoning_overrides=role_reasoning_overrides,
            eval_profile=eval_profile,
            reference_images_enabled=reference_images_enabled,
        )
    )


async def _run_case(
    *,
    case: EvalCase,
    case_dir: Path,
    config: HarnessConfig,
    profile: str | None,
    model: str | None,
    effort: str | None,
    max_revisions: int | None,
    role_model_overrides: dict[str, str] | None,
    role_reasoning_overrides: dict[str, str] | None,
    eval_profile: Profile,
    reference_images_enabled: bool,
) -> dict[str, Any]:
    case_dir.mkdir(parents=True, exist_ok=True)
    reference_image = (
        str(case.reference_image) if reference_images_enabled and case.reference_image else None
    )
    _write_json(
        case_dir / "case.json",
        {
            "case_id": case.case_id,
            "prompt": case.prompt,
            "ground_truth_step": str(case.ground_truth_step),
            "reference_image": str(case.reference_image) if case.reference_image else None,
            "reference_image_used": reference_image is not None,
        },
    )
    rec = _case_record(case=case, reference_images_enabled=reference_images_enabled)
    current_stage = STAGE_RUN_STARTED

    try:
        rec["stages"][STAGE_RUN_STARTED] = True
        driver = RunDriver(config)
        result = await driver.run(
            DriveRequest(
                prompt=case.prompt,
                profile_name=profile,
                model_override=model,
                reasoning_override=effort,
                reference_image=reference_image,
                max_revisions=max_revisions,
                role_model_overrides=role_model_overrides,
                role_reasoning_overrides=role_reasoning_overrides,
            )
        )
        _write_json(case_dir / "drive-result.json", result)
        rec.update(
            {
                "run_name": result["run_name"],
                "status": result["status"],
                "delivered_revision": result["delivered_revision"],
            }
        )

        delivered = result.get("delivered_revision")
        current_stage = STAGE_REVISION_DELIVERED
        if not delivered:
            rec["error"] = _write_case_error(
                case_dir,
                stage=current_stage,
                message="run completed without a delivered revision",
            )
            return rec
        rec["stages"][STAGE_REVISION_DELIVERED] = True

        current_stage = STAGE_BUILD_ARTIFACTS_AVAILABLE
        if not _revision_artifacts_available(config, result["run_name"], delivered):
            rec["error"] = _write_case_error(
                case_dir,
                stage=current_stage,
                message="delivered revision is missing required STEP/GLB/render artifacts",
            )
            return rec
        rec["stages"][STAGE_BUILD_ARTIFACTS_AVAILABLE] = True

        current_stage = STAGE_COMPARE_COMPLETED
        cmp = cad_compare(
            left_path=case.ground_truth_step,
            right_path=_delivered_step(config, result["run_name"], delivered),
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
        rec["stages"][STAGE_COMPARE_COMPLETED] = True

        current_stage = STAGE_JUDGE_COMPLETED
        judge = await _judge_case(
            case=case,
            metrics=metrics,
            config=config,
            run_name=result["run_name"],
            delivered_revision=delivered,
            eval_profile=eval_profile,
            reference_images_enabled=reference_images_enabled,
        )
        judge_path = case_dir / "judge-output.json"
        judge_path.write_text(judge.model_dump_json(indent=2, by_alias=True))
        rec["judge"] = judge.model_dump(by_alias=True)
        rec["stages"][STAGE_JUDGE_COMPLETED] = True
    except Exception as exc:  # noqa: BLE001 -- preserve failed cases as benchmark signal.
        rec["status"] = "error" if rec["status"] == "not_started" else rec["status"]
        rec["error"] = _write_case_error(case_dir, stage=current_stage, exc=exc)
    return rec


async def _judge_case(
    *,
    case: EvalCase,
    metrics: DeterministicMetrics,
    config: HarnessConfig,
    run_name: str,
    delivered_revision: str,
    eval_profile: Profile,
    reference_images_enabled: bool,
) -> JudgeOutput:
    judge = build_judge(eval_profile)
    payload = {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "deterministic_metrics": metrics.model_dump(),
        "review_focus": {
            "primary_modality": "visual",
            "feature_checklist": "Use flexible, high-signal criteria implied by the prompt.",
        },
    }
    render_sheet = (
        config.runs_dir / run_name / "revisions" / delivered_revision / "render-sheet.png"
    )
    images = [render_sheet]
    if reference_images_enabled and case.reference_image:
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
