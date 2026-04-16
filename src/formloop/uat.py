from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from formloop.models import DesignRequest, ReferenceImage
from formloop.service import HarnessService
from formloop.types import ArtifactKind, RunStatus


def run_uat(service: HarnessService, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    reference_path = report_dir / "reference.png"
    Image.new("RGB", (32, 32), (210, 210, 210)).save(reference_path)

    cases = [
        (
            "UAT-001",
            DesignRequest(prompt="Create a block width 40 height 20 depth 10 for a mounting spacer."),
            lambda run: (
                run.status == RunStatus.SUCCEEDED
                and any(a.kind == ArtifactKind.RENDER_SHEET for a in run.final_artifacts)
                and run.latest_review_summary is not None
            ),
        ),
        (
            "UAT-002",
            DesignRequest(prompt="Create some part for a thing with exact fit."),
            lambda run: run.status == RunStatus.NEEDS_CLARIFICATION and bool(run.clarifications),
        ),
        (
            "UAT-003",
            DesignRequest(prompt="Create a block mount for a fixture."),
            lambda run: run.status == RunStatus.SUCCEEDED and bool(run.assumptions),
        ),
        (
            "UAT-004",
            DesignRequest(prompt="Create a bracket for an M3 fastener mount width 40 height 30 thickness 5."),
            lambda run: run.status == RunStatus.SUCCEEDED and any("M3" in event.message or "m3" in str(event.payload).lower() for event in run.trace_events),
        ),
        (
            "UAT-005",
            DesignRequest(
                prompt="Create a bracket for an M3 fastener mount width 40 height 30 thickness 5 using the reference image.",
                reference_image=ReferenceImage(path=str(reference_path), label="uat-reference"),
            ),
            lambda run: run.status == RunStatus.SUCCEEDED and any(a.kind == ArtifactKind.REFERENCE_IMAGE for a in run.final_artifacts),
        ),
        (
            "UAT-006",
            DesignRequest(prompt="Create a bracket for an M3 fastener mount width 40 height 30 thickness 5 with undersize holes."),
            lambda run: run.status == RunStatus.SUCCEEDED and len(run.revisions) == 2,
        ),
    ]

    lines = ["# UAT Report", ""]
    for case_id, request, assertion in cases:
        run = service.execute_run(request)
        passed = assertion(run)
        lines.append(f"## {case_id}")
        lines.append("")
        lines.append(f"- Status: {'PASS' if passed else 'FAIL'}")
        lines.append(f"- Run ID: {run.run_id}")
        lines.append(f"- Run status: {run.status.value}")
        lines.append("")
        if not passed:
            raise AssertionError(f"{case_id} failed")

    normal_run = service.execute_run(
        DesignRequest(prompt="Create a block width 30 height 10 depth 8 for a profile-aware smoke run.", profile="normal")
    )
    anthropic_run = service.execute_run(
        DesignRequest(prompt="Create a block width 30 height 10 depth 8 for a profile-aware smoke run.", profile="anthropic_normal")
    )
    uat_007 = (
        normal_run.status == RunStatus.SUCCEEDED
        and anthropic_run.status == RunStatus.SUCCEEDED
        and normal_run.effective_runtime.provider == "openai_responses"
        and anthropic_run.effective_runtime.provider == "litellm"
    )
    lines.extend(
        [
            "## UAT-007",
            "",
            f"- Status: {'PASS' if uat_007 else 'FAIL'}",
            f"- Normal provider: {normal_run.effective_runtime.provider}",
            f"- Anthropic provider: {anthropic_run.effective_runtime.provider}",
            "",
        ]
    )
    if not uat_007:
        raise AssertionError("UAT-007 failed")

    eval_batch = service.execute_eval("basic_shapes", profile_name="eval")
    uat_008 = bool(eval_batch.case_results) and "case_count" in eval_batch.aggregate_metrics
    lines.extend(
        [
            "## UAT-008",
            "",
            f"- Status: {'PASS' if uat_008 else 'FAIL'}",
            f"- Aggregate metrics: {eval_batch.aggregate_metrics}",
            f"- Report path: {eval_batch.report_path}",
            "",
        ]
    )
    if not uat_008:
        raise AssertionError("UAT-008 failed")

    original_anthropic = os.environ.get("ANTHROPIC_API_KEY")
    try:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        missing_doctor = service.doctor(["anthropic_normal"])
    finally:
        if original_anthropic is not None:
            os.environ["ANTHROPIC_API_KEY"] = original_anthropic
    healthy_doctor = service.doctor(["normal", "anthropic_normal"])
    uat_009 = (missing_doctor["ok"] is False) and (healthy_doctor["ok"] is True)
    lines.extend(
        [
            "## UAT-009",
            "",
            f"- Status: {'PASS' if uat_009 else 'FAIL'}",
            f"- Missing-key issues: {missing_doctor['issues']}",
            f"- Healthy doctor issues: {healthy_doctor['issues']}",
            "",
        ]
    )
    if not uat_009:
        raise AssertionError("UAT-009 failed")

    trace_run = service.execute_run(
        DesignRequest(
            prompt="Create a bracket for an M3 fastener mount width 40 height 30 thickness 5 using the reference image.",
            reference_image=ReferenceImage(path=str(reference_path), label="trace-reference"),
        )
    )
    uat_010 = (
        trace_run.status == RunStatus.SUCCEEDED
        and trace_run.current_spec is not None
        and bool(trace_run.trace_events)
        and bool(trace_run.subagent_calls)
        and bool(trace_run.tool_calls)
        and any(a.kind == ArtifactKind.REFERENCE_IMAGE for a in trace_run.final_artifacts)
        and any(a.kind == ArtifactKind.STEP for a in trace_run.final_artifacts)
    )
    lines.extend(
        [
            "## UAT-010",
            "",
            f"- Status: {'PASS' if uat_010 else 'FAIL'}",
            f"- Trace events: {len(trace_run.trace_events)}",
            f"- Subagent calls: {len(trace_run.subagent_calls)}",
            f"- Tool calls: {len(trace_run.tool_calls)}",
            "",
        ]
    )
    if not uat_010:
        raise AssertionError("UAT-010 failed")

    report_path = report_dir / "latest.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
