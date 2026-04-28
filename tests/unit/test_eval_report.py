from __future__ import annotations

import json
from pathlib import Path

from formloop.config.profiles import ApiConfig, HarnessConfig, Profile, Timeouts
from formloop.evals.report import render_report
from formloop.evals.runner import OUTCOME_STAGES, _aggregate


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


def test_render_report_includes_aggregate_metrics_and_incomplete_cases(tmp_path: Path) -> None:
    config = _config(tmp_path)
    batch = config.evals_dir / "batch"
    batch.mkdir(parents=True)
    cases = [
        {
            "case_id": "cube",
            "status": "succeeded",
            "delivered_revision": "rev-001",
            "metrics": {"overlap_ratio": 1.0},
            "judge": {"pass": True, "overall_score": 1.0},
            "stages": {stage: True for stage in OUTCOME_STAGES},
        },
        {
            "case_id": "bad",
            "status": "failed",
            "delivered_revision": None,
            "metrics": None,
            "judge": None,
            "stages": {stage: False for stage in OUTCOME_STAGES},
        },
    ]
    (batch / "batch-summary.json").write_text(
        json.dumps(
            {
                "batch_name": "batch",
                "dataset": "datasets/basic_shapes/cases.jsonl",
                "workers": 5,
                "reference_images_enabled": True,
                "effective_runtime": {
                    "profile": "normal",
                    "model": "base-model",
                    "reasoning": "medium",
                    "roles": {},
                },
                "aggregate": _aggregate(cases),
                "cases": cases,
            }
        )
    )

    report_path = render_report(config, "batch")
    text = report_path.read_text()

    assert "Run success rate: 1/2 (50.0%)" in text
    assert "Judge pass rate: 1/1 (100.0%)" in text
    assert "| bad | failed | - | no | no | no | - | - | - |" in text
