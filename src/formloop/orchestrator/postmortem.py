"""Post-mortem orchestration — collect run context and invoke the agent.

REQ: FLH-NF-007, FLH-V-003

Pure deterministic helpers for assembling the post-mortem prompt payload from
a persisted run, plus the entrypoint that drives the post-mortem agent and
writes its outputs into the run directory.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..agents.common import Runner
from ..agents.postmortem import RunPostMortem, build_postmortem_agent
from ..config.profiles import Profile


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _clip(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def _agent_timings(run_log: str) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for name, elapsed in re.findall(r"agent end: ([a-z_]+) elapsed=([0-9.]+)s", run_log):
        out.setdefault(name, []).append(float(elapsed))
    return out


def collect_run_postmortem_context(runs_dir: Path, run_name: str) -> dict[str, Any]:
    run_root = runs_dir / run_name
    run = _read_json(run_root / "run.json")
    snapshot = (
        _read_json(run_root / "snapshot.json") if (run_root / "snapshot.json").is_file() else {}
    )
    run_log = (run_root / "run.log").read_text(encoding="utf-8", errors="replace")

    events: list[dict[str, Any]] = []
    events_path = run_root / "events.jsonl"
    if events_path.is_file():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("kind") in {
                "spec_normalized",
                "research_completed",
                "cad_source_authored",
                "cad_validation_failed",
                "cad_validation_completed",
                "revision_built",
                "revision_persisted",
                "review_completed",
                "delivered",
                "run_failed",
            }:
                events.append(event)

    source_attempts: list[dict[str, Any]] = []
    attempts_root = run_root / "_work" / "source_attempts"
    if attempts_root.is_dir():
        for attempt_dir in sorted(attempts_root.glob("attempt-*")):
            attempt_item: dict[str, Any] = {"attempt": attempt_dir.name}
            for filename, key in (
                ("validation-result.json", "validation"),
                ("failure-feedback.json", "failure_feedback"),
            ):
                path = attempt_dir / filename
                if path.is_file():
                    attempt_item[key] = _read_json(path)
            source_attempts.append(attempt_item)

    reviews: list[dict[str, Any]] = []
    revisions_root = run_root / "revisions"
    if revisions_root.is_dir():
        for rev_dir in sorted(revisions_root.glob("rev-*")):
            review_path = rev_dir / "review-summary.json"
            inspect_path = rev_dir / "inspect-summary.json"
            review_item: dict[str, Any] = {"revision": rev_dir.name}
            if review_path.is_file():
                review_item["review"] = _read_json(review_path)
            if inspect_path.is_file():
                inspect = _read_json(inspect_path)
                review_item["inspect_summary"] = inspect.get("summary")
                review_item["inspect_data"] = {
                    key: inspect.get("data", {}).get(key)
                    for key in ("bounding_box", "solid_count", "volume")
                }
            reviews.append(review_item)

    return {
        "run": {
            "run_name": run_name,
            "status": run.get("status"),
            "status_detail": run.get("status_detail"),
            "revisions": run.get("revisions"),
            "current_revision_id": run.get("current_revision_id"),
            "effective_runtime": run.get("effective_runtime"),
            "current_spec": run.get("current_spec"),
        },
        "snapshot": {
            "latest_review_decision": snapshot.get("latest_review_decision"),
            "last_event_kind": snapshot.get("last_event_kind"),
            "last_message": snapshot.get("last_message"),
        },
        "timings": _agent_timings(run_log),
        "events": events,
        "source_attempts": source_attempts,
        "reviews": reviews,
        "run_log_tail": _clip("\n".join(run_log.splitlines()[-120:])),
    }


def write_postmortem_issues_markdown(postmortem: RunPostMortem, path: Path) -> Path:
    lines = [f"# Run post-mortem — {postmortem.run_name}", "", postmortem.summary, ""]
    for idx, issue in enumerate(postmortem.key_issues, start=1):
        labels = ", ".join(issue.labels) if issue.labels else issue.category
        lines.extend(
            [
                f"## {idx}. {issue.title}",
                "",
                f"- Severity: `{issue.severity}`",
                f"- Category: `{issue.category}`",
                f"- Labels: `{labels}`",
                "",
                "### Impact",
                issue.impact,
                "",
                "### Evidence",
            ]
        )
        lines.extend(f"- {e}" for e in issue.evidence or ["No specific evidence provided."])
        lines.extend(["", "### Suggested Fix", issue.suggested_fix, "", "### Acceptance Criteria"])
        lines.extend(f"- {a}" for a in issue.acceptance_criteria or ["Fix is validated."])
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


async def run_postmortem(
    *,
    runs_dir: Path,
    run_name: str,
    output_dir: Path,
    profile: Profile,
) -> RunPostMortem:
    context = collect_run_postmortem_context(runs_dir, run_name)
    agent = build_postmortem_agent(profile)
    result = await Runner.run(
        agent,
        input=(
            "Create a Formloop harness optimization post-mortem from this run data:\n\n"
            + json.dumps(context, indent=2, default=str)
        ),
    )
    postmortem = result.final_output
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run-postmortem.json").write_text(
        postmortem.model_dump_json(indent=2), encoding="utf-8"
    )
    write_postmortem_issues_markdown(postmortem, output_dir / "run-postmortem-issues.md")
    return postmortem


__all__ = [
    "collect_run_postmortem_context",
    "run_postmortem",
    "write_postmortem_issues_markdown",
]
