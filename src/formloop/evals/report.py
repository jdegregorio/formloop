"""Render a batch report (FLH-F-014, FLH-NF-003)."""

from __future__ import annotations

import json
from pathlib import Path

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


def render_report(config: HarnessConfig, batch: str) -> Path:
    batch_dir = _resolve_batch(config, batch)
    summary_path = batch_dir / "batch-summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"no batch-summary.json in {batch_dir}")
    summary = json.loads(summary_path.read_text())

    lines: list[str] = []
    lines.append(f"# Eval report — {summary['batch_name']}\n")
    lines.append(f"- Dataset: `{summary['dataset']}`")
    lines.append(f"- Profile: `{summary['profile']}`")
    lines.append(f"- Cases: {len(summary['cases'])}\n")

    lines.append("## Results\n")
    lines.append(
        "| case_id | status | delivered | overlap_ratio | judge.pass | judge.overall |"
    )
    lines.append("|---|---|---|---|---|---|")
    agreements = 0
    total = 0
    passes = 0
    for case in summary["cases"]:
        metrics = case.get("metrics") or {}
        judge = case.get("judge") or {}
        overlap = metrics.get("overlap_ratio")
        overlap_s = f"{overlap:.3f}" if isinstance(overlap, int | float) else "—"
        judge_pass = judge.get("pass") if "pass" in judge else None
        judge_overall = judge.get("overall_score")
        overall_s = f"{judge_overall:.2f}" if isinstance(judge_overall, int | float) else "—"
        pass_s = "✓" if judge_pass else ("✗" if judge_pass is False else "—")
        lines.append(
            f"| {case['case_id']} | {case['status']} | "
            f"{case.get('delivered_revision') or '—'} | {overlap_s} | {pass_s} | "
            f"{overall_s} |"
        )
        if judge_pass is not None:
            total += 1
            if judge_pass:
                passes += 1
            if overlap is not None and (overlap >= 0.95) == bool(judge_pass):
                agreements += 1

    lines.append("")
    lines.append(f"- Judge pass rate: {passes}/{total}" if total else "- No judged cases")
    if total:
        lines.append(f"- Deterministic-vs-judge agreement: {agreements}/{total}")

    out = batch_dir / "batch-report.md"
    out.write_text("\n".join(lines) + "\n")
    return out
