"""Render a batch report (FLH-F-014, FLH-NF-003)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config.profiles import HarnessConfig


def _resolve_batch(config: HarnessConfig, batch: str) -> Path:
    if batch == "latest":
        ptr = config.evals_dir / "latest.txt"
        if not ptr.is_file():
            raise FileNotFoundError("no evals have run yet (no latest.txt)")
        batch = ptr.read_text().strip()
    path = config.evals_dir / batch
    if not path.is_dir():
        raise FileNotFoundError(f"batch not found: {path}")
    return path


def _format_rate(metric: dict[str, Any] | None) -> str:
    if not metric:
        return "n/a"
    passed = metric.get("passed")
    total = metric.get("total")
    rate = metric.get("rate")
    if rate is None:
        return f"{passed}/{total}"
    return f"{passed}/{total} ({rate:.1%})"


def _stage_mark(case: dict[str, Any], stage: str) -> str:
    return "yes" if (case.get("stages") or {}).get(stage) else "no"


def render_report(config: HarnessConfig, batch: str) -> Path:
    batch_dir = _resolve_batch(config, batch)
    summary_path = batch_dir / "batch-summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"no batch-summary.json in {batch_dir}")
    summary = json.loads(summary_path.read_text())

    lines: list[str] = []
    lines.append(f"# Eval report — {summary['batch_name']}\n")
    lines.append(f"- Dataset: `{summary['dataset']}`")
    requested_workers = summary.get("requested_workers")
    effective_workers = summary.get("workers", "n/a")
    if requested_workers is None:
        lines.append(f"- Workers: `{effective_workers}`")
    else:
        lines.append(f"- Workers: requested `{requested_workers}`, effective `{effective_workers}`")
    if summary.get("worker_warning"):
        lines.append(f"- Worker warning: {summary['worker_warning']}")
    lines.append(f"- Reference images: `{summary.get('reference_images_enabled', 'n/a')}`")
    runtime = summary.get("effective_runtime") or {}
    if runtime:
        lines.append(
            f"- Runtime: `{runtime.get('profile')}` / `{runtime.get('model')}` / "
            f"`{runtime.get('reasoning')}`"
        )
    lines.append(f"- Cases: {len(summary['cases'])}\n")

    aggregate = summary.get("aggregate") or {}
    lines.append("## Aggregate Metrics\n")
    lines.append(f"- Run success rate: {_format_rate(aggregate.get('run_success'))}")
    lines.append(f"- Delivered revision rate: {_format_rate(aggregate.get('revision_delivered'))}")
    lines.append(
        f"- Build/artifact availability rate: "
        f"{_format_rate(aggregate.get('build_artifacts_available'))}"
    )
    lines.append(f"- Compare completion rate: {_format_rate(aggregate.get('compare_completed'))}")
    lines.append(f"- Judge completion rate: {_format_rate(aggregate.get('judge_completed'))}")
    lines.append(f"- Judge pass rate: {_format_rate(aggregate.get('judge_pass'))}")
    lines.append(
        f"- Deterministic-vs-judge agreement: "
        f"{_format_rate(aggregate.get('deterministic_judge_agreement'))}"
    )

    lines.append("\n## Results\n")
    lines.append(
        "| case_id | status | delivered | artifacts | compare | judge | "
        "overlap_ratio | judge.pass | judge.overall |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for case in summary["cases"]:
        metrics = case.get("metrics") or {}
        judge = case.get("judge") or {}
        overlap = metrics.get("overlap_ratio")
        overlap_s = f"{overlap:.3f}" if isinstance(overlap, int | float) else "-"
        judge_pass = judge.get("pass") if "pass" in judge else None
        judge_overall = judge.get("overall_score")
        overall_s = f"{judge_overall:.2f}" if isinstance(judge_overall, int | float) else "-"
        pass_s = "yes" if judge_pass else ("no" if judge_pass is False else "-")
        lines.append(
            f"| {case['case_id']} | {case['status']} | "
            f"{case.get('delivered_revision') or '-'} | "
            f"{_stage_mark(case, 'build_artifacts_available')} | "
            f"{_stage_mark(case, 'compare_completed')} | "
            f"{_stage_mark(case, 'judge_completed')} | "
            f"{overlap_s} | {pass_s} | {overall_s} |"
        )

    out = batch_dir / "batch-report.md"
    out.write_text("\n".join(lines) + "\n")
    return out
