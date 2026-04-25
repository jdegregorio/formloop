"""Unit tests for run post-mortem artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from formloop.agents.postmortem import PostMortemIssue, RunPostMortem
from formloop.orchestrator.postmortem import (
    collect_run_postmortem_context,
    write_postmortem_issues_markdown,
)


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_collect_run_postmortem_context_includes_latency_and_cad_failures(tmp_path) -> None:
    run = tmp_path / "runs" / "run-0001"
    _write(
        run / "run.json",
        {
            "run_name": "run-0001",
            "status": "failed",
            "status_detail": "max revisions exhausted",
            "revisions": ["rev-001"],
            "current_revision_id": "rev-001",
            "effective_runtime": {"profile": "normal", "model": "gpt-5.4", "reasoning": "medium"},
            "current_spec": {"key_dimension_parameters": {"overall_width": 20}},
        },
    )
    _write(run / "snapshot.json", {"latest_review_decision": "revise"})
    _write(
        run / "run.log",
        "\n".join(
            [
                "2026 INFO x: agent end: manager_planner elapsed=10.00s",
                "2026 INFO x: agent end: cad_designer elapsed=120.50s",
            ]
        ),
    )
    _write(
        run / "events.jsonl",
        json.dumps(
            {
                "index": 1,
                "kind": "cad_validation_failed",
                "message": "build failed",
                "data": {"failed_phase": "build"},
            }
        )
        + "\n",
    )
    _write(
        run / "_work" / "source_attempts" / "attempt-001" / "failure-feedback.json",
        {"failed_phase": "build", "detail": "TypeError: Invalid key for Rotation"},
    )
    _write(
        run / "_work" / "source_attempts" / "attempt-001" / "validation-result.json",
        {"ok": False, "commands": [{"command": "cad build", "duration_s": 1.2}]},
    )

    ctx = collect_run_postmortem_context(tmp_path / "runs", "run-0001")

    assert ctx["run"]["status"] == "failed"
    assert ctx["timings"]["cad_designer"] == [120.5]
    assert ctx["source_attempts"][0]["failure_feedback"]["failed_phase"] == "build"
    assert ctx["events"][0]["kind"] == "cad_validation_failed"


def test_write_postmortem_issues_markdown(tmp_path) -> None:
    postmortem = RunPostMortem(
        run_name="run-0001",
        summary="Run was slow because CAD source repairs repeated.",
        key_issues=[
            PostMortemIssue(
                title="Add deterministic width gate",
                category="quality",
                severity="high",
                evidence=["review caught width after expensive render"],
                impact="Avoids wasted review calls.",
                suggested_fix="Check inspect bbox before review.",
                acceptance_criteria=["Bad width creates source feedback before render."],
                labels=["harness", "quality-gate"],
            )
        ],
    )

    out = write_postmortem_issues_markdown(postmortem, tmp_path / "issues.md")
    text = out.read_text()

    assert "Add deterministic width gate" in text
    assert "quality-gate" in text
    assert "Bad width creates source feedback" in text
