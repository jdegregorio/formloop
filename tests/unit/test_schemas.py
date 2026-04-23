"""Schema round-trip and contract tests.

REQ: FLH-D-021, FLH-D-022, FLH-V-001
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from formloop.schemas import (
    ArtifactEntry,
    ArtifactManifest,
    AssumptionRecord,
    DeterministicMetrics,
    EffectiveRuntime,
    JudgeOutput,
    ProgressEvent,
    ProgressEventKind,
    ReviewDecision,
    ReviewSummary,
    Revision,
    RevisionTrigger,
    Run,
    RunCreateRequest,
    RunCreateResponse,
    RunSnapshot,
    RunStatus,
)


def test_run_roundtrip() -> None:
    run = Run(
        run_id="uuid-1",
        run_name="run-0001",
        input_summary="make a cube",
        effective_runtime=EffectiveRuntime(profile="normal", model="gpt-5.4", reasoning="high"),
        assumptions=[AssumptionRecord(topic="size", assumption="default 20mm")],
    )
    blob = run.model_dump_json()
    restored = Run.model_validate_json(blob)
    assert restored == run
    assert restored.status == RunStatus.created


def test_revision_requires_ordinal_and_trigger() -> None:
    rev = Revision(
        revision_id="uuid-r1",
        revision_name="rev-001",
        ordinal=1,
        trigger=RevisionTrigger.initial,
        artifact_manifest_path="rev-001/artifact-manifest.json",
    )
    assert rev.trigger is RevisionTrigger.initial
    assert rev.ordinal == 1


def test_artifact_manifest_entries() -> None:
    manifest = ArtifactManifest(
        revision_name="rev-001",
        entries=[
            ArtifactEntry(role="step", path="step.step", format="step"),
            ArtifactEntry(role="glb", path="model.glb", format="glb"),
        ],
    )
    assert {e.role for e in manifest.entries} == {"step", "glb"}


def test_review_summary_decision_enum() -> None:
    rs = ReviewSummary(
        decision=ReviewDecision.pass_,
        confidence=0.92,
        key_findings=["looks right"],
        feature_checklist=[{"feature": "overall silhouette", "status": "pass"}],
    )
    assert rs.decision is ReviewDecision.pass_
    assert rs.feature_checklist[0]["feature"] == "overall silhouette"
    # Revise requires concrete instructions in practice; schema doesn't enforce
    # but the field defaults to "".
    assert rs.revision_instructions == ""


def test_progress_event_kinds_cover_lifecycle() -> None:
    kinds = {k.value for k in ProgressEventKind}
    required = {
        "run_created",
        "spec_normalized",
        "revision_persisted",
        "review_completed",
        "narration",
        "delivered",
        "run_failed",
    }
    missing = required - kinds
    assert not missing, f"ProgressEventKind missing: {missing}"


def test_progress_event_index_must_be_nonneg() -> None:
    with pytest.raises(ValueError):
        ProgressEvent(index=-1, kind=ProgressEventKind.run_created)


def test_progress_event_narration_round_trip() -> None:
    # REQ: FLH-F-026 — narration carries phase + optional fallback error.
    ev = ProgressEvent(
        index=4,
        kind=ProgressEventKind.narration,
        message="we normalized the spec",
        phase="plan",
        narration_error=None,
    )
    blob = ev.model_dump_json()
    restored = ProgressEvent.model_validate_json(blob)
    assert restored == ev
    assert restored.kind is ProgressEventKind.narration
    assert restored.phase == "plan"


def test_run_snapshot_default_artifacts_empty() -> None:
    snap = RunSnapshot(run_id="u", run_name="run-0001", status="running")
    assert snap.artifacts.step_path is None
    assert snap.last_event_index == -1
    # REQ: FLH-F-026 — narration fields are present and default empty.
    assert snap.latest_narration is None
    assert snap.latest_narration_phase is None
    assert snap.latest_narration_index is None


def test_deterministic_metrics_optional_volumes() -> None:
    m = DeterministicMetrics(case_id="cube_20mm", mode="exact", alignment="principal")
    assert m.left_volume is None
    assert m.overlap_ratio is None


def test_judge_output_pass_field_alias() -> None:
    payload = {
        "case_id": "cube_20mm",
        "overall_score": 0.88,
        "pass": True,
        "rationale": "matches",
    }
    jo = JudgeOutput.model_validate(payload)
    assert jo.pass_ is True
    # Round-trip must emit the alias 'pass', not 'pass_', so it stays valid JSON
    round_tripped = json.loads(jo.model_dump_json(by_alias=True))
    assert "pass" in round_tripped


def test_run_create_request_defaults_profile_normal() -> None:
    req = RunCreateRequest(prompt="a cube")
    assert req.profile == "normal"


def test_run_create_response_fields() -> None:
    r = RunCreateResponse(
        run_id="u",
        run_name="run-0001",
        status_url="/runs/run-0001/snapshot",
        events_url="/runs/run-0001/events",
    )
    assert r.status_url.endswith("/snapshot")


def test_checked_in_schemas_match_pydantic() -> None:
    """schemas/*.schema.json must stay in sync with the Pydantic mirrors."""
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/sync_schemas.py", "--check"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"schemas out of date: {result.stderr}"


def test_all_checked_in_schemas_are_valid_json() -> None:
    repo = Path(__file__).resolve().parents[2]
    files = sorted((repo / "schemas").glob("*.schema.json"))
    assert len(files) == 10, f"expected 10 schemas, got {len(files)}"
    for f in files:
        data = json.loads(f.read_text())
        assert data["$schema"].startswith("https://json-schema.org/")
        assert data["$id"].startswith("formloop/")
