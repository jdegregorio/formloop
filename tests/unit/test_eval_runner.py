from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from formloop.config.profiles import ApiConfig, HarnessConfig, Profile, Timeouts
from formloop.evals.runner import (
    DEFAULT_WORKERS,
    OUTCOME_STAGES,
    STAGE_BUILD_ARTIFACTS_AVAILABLE,
    STAGE_REVISION_DELIVERED,
    _aggregate,
    run_eval_batch,
)


def _config(tmp_path: Path) -> HarnessConfig:
    return HarnessConfig(
        default_profile="normal",
        max_revisions=3,
        max_research_topics=8,
        runs_dir=tmp_path / "runs",
        evals_dir=tmp_path / "evals",
        timeouts=Timeouts(
            cad_build=1,
            cad_render=1,
            cad_inspect=1,
            cad_compare=1,
            agent_run=1,
        ),
        profiles={"normal": Profile(name="normal", model="base-model", reasoning="medium")},
        api=ApiConfig(host="127.0.0.1", port=0, pid_file="x.pid", log_file="x.log"),
        repo_root=tmp_path,
    )


def _write_cases(path: Path, count: int) -> None:
    rows = [
        {
            "case_id": f"case_{index}",
            "prompt": f"prompt {index}",
            "ground_truth_step": f"ground_truth/case_{index}.step",
        }
        for index in range(count)
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _successful_record(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "run_name": f"run-{case_id}",
        "status": "succeeded",
        "delivered_revision": "rev-001",
        "metrics": {"overlap_ratio": 1.0},
        "judge": {"pass": True, "overall_score": 1.0},
        "stages": {stage: True for stage in OUTCOME_STAGES},
        "reference_image_available": False,
        "reference_image_used": False,
        "error": None,
    }


@pytest.mark.asyncio
async def test_run_eval_batch_serializes_case_execution_and_preserves_order(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    dataset = tmp_path / "cases.jsonl"
    _write_cases(dataset, 5)
    active = 0
    max_active = 0
    lock = threading.Lock()

    def fake_run_case_in_thread(**kwargs):
        nonlocal active, max_active
        case = kwargs["case"]
        kwargs["case_dir"].mkdir(parents=True, exist_ok=True)
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return _successful_record(case.case_id)

    monkeypatch.setattr("formloop.evals.runner._run_case_in_thread", fake_run_case_in_thread)

    summary_path = await run_eval_batch(
        dataset_path=dataset,
        config=config,
        batch_name="parallel",
        workers=2,
    )

    summary = json.loads(summary_path.read_text())
    assert summary["requested_workers"] == 2
    assert summary["workers"] == 1
    assert "parallel case execution is temporarily disabled" in summary["worker_warning"]
    assert [case["case_id"] for case in summary["cases"]] == [f"case_{i}" for i in range(5)]
    assert max_active == 1


@pytest.mark.asyncio
async def test_run_eval_batch_keeps_partial_failures_and_aggregates_metrics(
    tmp_path: Path, monkeypatch
) -> None:
    config = _config(tmp_path)
    dataset = tmp_path / "cases.jsonl"
    _write_cases(dataset, 3)

    def fake_run_case_in_thread(**kwargs):
        case = kwargs["case"]
        kwargs["case_dir"].mkdir(parents=True, exist_ok=True)
        if case.case_id == "case_1":
            raise RuntimeError("boom")
        return _successful_record(case.case_id)

    monkeypatch.setattr("formloop.evals.runner._run_case_in_thread", fake_run_case_in_thread)

    summary_path = await run_eval_batch(
        dataset_path=dataset,
        config=config,
        batch_name="partial",
        workers=DEFAULT_WORKERS,
        reference_images_enabled=False,
    )

    summary = json.loads(summary_path.read_text())
    assert summary["reference_images_enabled"] is False
    assert [case["case_id"] for case in summary["cases"]] == ["case_0", "case_1", "case_2"]
    assert summary["cases"][1]["status"] == "error"
    assert (config.evals_dir / "partial" / "case_1" / "case-error.json").is_file()
    assert summary["aggregate"]["run_success"] == {"passed": 2, "total": 3, "rate": 0.666667}
    assert summary["aggregate"]["judge_pass"] == {"passed": 2, "total": 2, "rate": 1.0}


def test_aggregate_tracks_stage_completion_rates() -> None:
    cases = [
        _successful_record("ok"),
        {
            **_successful_record("built_only"),
            "status": "failed",
            "metrics": None,
            "judge": None,
            "stages": {
                stage: stage
                in {
                    STAGE_REVISION_DELIVERED,
                    STAGE_BUILD_ARTIFACTS_AVAILABLE,
                }
                for stage in OUTCOME_STAGES
            },
        },
        {
            **_successful_record("no_revision"),
            "status": "failed",
            "delivered_revision": None,
            "metrics": None,
            "judge": None,
            "stages": {stage: False for stage in OUTCOME_STAGES},
        },
    ]

    aggregate = _aggregate(cases)

    assert aggregate["revision_delivered"] == {"passed": 2, "total": 3, "rate": 0.666667}
    assert aggregate["build_artifacts_available"] == {"passed": 2, "total": 3, "rate": 0.666667}
    assert aggregate["compare_completed"] == {"passed": 1, "total": 3, "rate": 0.333333}
    assert aggregate["judge_completed"] == {"passed": 1, "total": 3, "rate": 0.333333}
    assert aggregate["judge_pass"] == {"passed": 1, "total": 1, "rate": 1.0}


@pytest.mark.asyncio
async def test_run_eval_batch_rejects_existing_nonempty_batch(tmp_path: Path) -> None:
    config = _config(tmp_path)
    dataset = tmp_path / "cases.jsonl"
    _write_cases(dataset, 1)
    existing = config.evals_dir / "existing"
    existing.mkdir(parents=True)
    (existing / "old.txt").write_text("old")

    with pytest.raises(FileExistsError, match="already exists"):
        await run_eval_batch(dataset_path=dataset, config=config, batch_name="existing")
