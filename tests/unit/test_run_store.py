"""Unit tests for RunStore persistence.

REQ: FLH-F-009, FLH-F-011, FLH-F-021, FLH-F-022, FLH-F-024
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from formloop.schemas import (
    EffectiveRuntime,
    ProgressEvent,
    ProgressEventKind,
    ReviewDecision,
    ReviewSummary,
    RevisionTrigger,
)
from formloop.store import RunStore
from formloop.store.run_store import CandidateBundle


@pytest.fixture()
def store(tmp_path: Path) -> RunStore:
    return RunStore(runs_root=tmp_path / "runs")


@pytest.fixture()
def effective_runtime() -> EffectiveRuntime:
    return EffectiveRuntime(profile="dev_test", model="gpt-5.4-nano", reasoning="low")


def _make_bundle(tmp: Path, trigger: RevisionTrigger = RevisionTrigger.initial) -> CandidateBundle:
    src = tmp / "src"
    src.mkdir(parents=True, exist_ok=True)
    step = src / "step.step"
    step.write_text("ISO-STEP\n")
    glb = src / "model.glb"
    glb.write_bytes(b"\x00glb")
    sheet = src / "render-sheet.png"
    sheet.write_bytes(b"\x89PNG\r\n\x1a\nsheet")
    views = src / "views"
    views.mkdir()
    for name in ("front", "back", "top"):
        (views / f"{name}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + name.encode())
    build_meta = src / "build.json"
    build_meta.write_text(json.dumps({"status": "ok"}))
    inspect = src / "inspect.json"
    inspect.write_text(json.dumps({"status": "ok", "mode": "exact"}))
    return CandidateBundle(
        trigger=trigger,
        spec_snapshot={"kind": "cube", "size": 20},
        designer_notes="Initial cube attempt.",
        known_risks=[],
        step_src=step,
        glb_src=glb,
        views_dir_src=views,
        render_sheet_src=sheet,
        build_metadata_src=build_meta,
        inspect_summary_src=inspect,
    )


def test_create_run_allocates_sequential_name(
    store: RunStore, effective_runtime: EffectiveRuntime
) -> None:
    run_a, layout_a = store.create_run(
        input_summary="cube", effective_runtime=effective_runtime
    )
    run_b, layout_b = store.create_run(
        input_summary="plate", effective_runtime=effective_runtime
    )
    assert run_a.run_name == "run-0001"
    assert run_b.run_name == "run-0002"
    assert layout_a.run_json.is_file()
    assert layout_a.events_jsonl.is_file()
    assert layout_a.snapshot_json.is_file()
    # First event recorded at creation.
    events = store.read_events(run_a.run_name)
    assert len(events) == 1
    assert events[0].kind == ProgressEventKind.run_created


def test_append_event_auto_indexes(
    store: RunStore, effective_runtime: EffectiveRuntime
) -> None:
    run, _ = store.create_run(input_summary="x", effective_runtime=effective_runtime)
    store.append_event(
        run.run_name,
        ProgressEvent(index=0, kind=ProgressEventKind.breadcrumb, message="a"),
    )
    store.append_event(
        run.run_name,
        ProgressEvent(index=0, kind=ProgressEventKind.breadcrumb, message="b"),
    )
    events = store.read_events(run.run_name)
    indices = [e.index for e in events]
    assert indices == [0, 1, 2]


def test_read_events_since_filters(
    store: RunStore, effective_runtime: EffectiveRuntime
) -> None:
    run, _ = store.create_run(input_summary="x", effective_runtime=effective_runtime)
    for _ in range(3):
        store.append_event(
            run.run_name,
            ProgressEvent(index=0, kind=ProgressEventKind.breadcrumb, message="hi"),
        )
    tail = store.read_events(run.run_name, since=2)
    assert [e.index for e in tail] == [2, 3]


def test_persist_revision_copies_bundle(
    store: RunStore, effective_runtime: EffectiveRuntime, tmp_path: Path
) -> None:
    run, layout = store.create_run(
        input_summary="cube", effective_runtime=effective_runtime
    )
    bundle = _make_bundle(tmp_path)
    revision, rev_layout = store.persist_revision(run, bundle)

    assert revision.revision_name == "rev-001"
    assert revision.ordinal == 1
    assert rev_layout.step.is_file()
    assert rev_layout.glb.is_file()
    assert rev_layout.render_sheet.is_file()
    assert rev_layout.revision_json.is_file()
    assert rev_layout.artifact_manifest.is_file()
    assert rev_layout.build_meta.is_file()
    assert rev_layout.inspect_summary.is_file()
    view_files = sorted(p.name for p in rev_layout.views_dir.glob("*.png"))
    assert view_files == ["back.png", "front.png", "top.png"]

    reloaded = store.load_run(run.run_name)
    assert reloaded.revisions == ["rev-001"]
    assert reloaded.current_revision_id == "rev-001"

    # Manifest records required + optional entries
    manifest = json.loads(rev_layout.artifact_manifest.read_text())
    roles = {e["role"] for e in manifest["entries"]}
    assert {"step", "glb", "render_sheet"}.issubset(roles)
    assert any(r.startswith("view_") for r in roles)
    assert "build_metadata" in roles
    assert "inspect_summary" in roles


def test_persist_revision_increments(
    store: RunStore, effective_runtime: EffectiveRuntime, tmp_path: Path
) -> None:
    run, _ = store.create_run(input_summary="cube", effective_runtime=effective_runtime)
    store.persist_revision(run, _make_bundle(tmp_path / "a"))
    rev2, _ = store.persist_revision(
        run, _make_bundle(tmp_path / "b", trigger=RevisionTrigger.review_revise)
    )
    assert rev2.revision_name == "rev-002"
    assert rev2.ordinal == 2
    reloaded = store.load_run(run.run_name)
    assert reloaded.revisions == ["rev-001", "rev-002"]
    assert reloaded.current_revision_id == "rev-002"


def test_attach_review_updates_snapshot(
    store: RunStore, effective_runtime: EffectiveRuntime, tmp_path: Path
) -> None:
    run, _ = store.create_run(input_summary="cube", effective_runtime=effective_runtime)
    revision, _ = store.persist_revision(run, _make_bundle(tmp_path))
    review = ReviewSummary(
        decision=ReviewDecision.pass_,
        confidence=0.9,
        key_findings=["Looks like a cube."],
    )
    store.attach_review(run, revision.revision_name, review)
    snap = store.load_snapshot(run.run_name)
    assert snap.latest_review_decision == ReviewDecision.pass_
    assert snap.current_revision_name == "rev-001"
    assert snap.artifacts is not None
    assert snap.artifacts.step_path is not None
    assert len(snap.artifacts.view_paths) == 3


def test_snapshot_tracks_last_event(
    store: RunStore, effective_runtime: EffectiveRuntime
) -> None:
    run, _ = store.create_run(input_summary="x", effective_runtime=effective_runtime)
    store.append_event(
        run.run_name,
        ProgressEvent(
            index=0, kind=ProgressEventKind.breadcrumb, message="hello world"
        ),
    )
    snap = store.load_snapshot(run.run_name)
    assert snap.last_event_kind == ProgressEventKind.breadcrumb.value
    assert snap.last_message == "hello world"
    assert snap.last_event_index >= 1


def test_atomic_write_leaves_no_tmp_file(
    store: RunStore, effective_runtime: EffectiveRuntime
) -> None:
    run, layout = store.create_run(
        input_summary="x", effective_runtime=effective_runtime
    )
    # No stray .tmp artifacts
    leftovers = list(layout.root.rglob("*.tmp"))
    assert leftovers == []
