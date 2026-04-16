from __future__ import annotations

from pathlib import Path

from PIL import Image

from formloop.models import DesignRequest, ReferenceImage
from formloop.types import ArtifactKind, ReviewDecision, RunStatus


def test_design_run_produces_closed_loop_artifacts(service) -> None:
    run = service.execute_run(DesignRequest(prompt="Create a block width 40 height 20 depth 10 for a mounting spacer."))
    assert run.status == RunStatus.SUCCEEDED
    assert run.current_spec is not None
    assert run.latest_review_summary is not None
    assert run.latest_review_summary.decision == ReviewDecision.PASS
    assert any(artifact.kind == ArtifactKind.STEP for artifact in run.final_artifacts)
    assert any(event.kind.value == "tool_call" for event in run.trace_events)
    assert run.tool_calls
    assert run.subagent_calls


def test_underspecified_request_triggers_clarification(service) -> None:
    run = service.execute_run(DesignRequest(prompt="Create some part for a thing with exact fit."))
    assert run.status == RunStatus.NEEDS_CLARIFICATION
    assert run.clarifications
    assert not run.revisions


def test_reference_image_and_research_are_recorded(service, tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.png"
    Image.new("RGB", (16, 16), (128, 128, 128)).save(reference_path)
    run = service.execute_run(
        DesignRequest(
            prompt="Create a bracket for an M3 fastener mount width 40 height 30 thickness 5 using the reference image.",
            reference_image=ReferenceImage(path=str(reference_path), label="fixture"),
        )
    )
    assert run.status == RunStatus.SUCCEEDED
    assert any(artifact.kind == ArtifactKind.REFERENCE_IMAGE for artifact in run.final_artifacts)
    assert any(event.kind.value == "research" for event in run.trace_events)
    assert run.latest_review_summary is not None
    assert run.latest_review_summary.reference_image_notes


def test_review_revision_loop_executes_second_iteration(service) -> None:
    run = service.execute_run(
        DesignRequest(prompt="Create a bracket for an M3 fastener mount width 40 height 30 thickness 5 with undersize holes.")
    )
    assert run.status == RunStatus.SUCCEEDED
    assert len(run.revisions) == 2
    assert run.revisions[0].review_summary.decision == ReviewDecision.REVISE
    assert run.revisions[1].review_summary.decision == ReviewDecision.PASS

