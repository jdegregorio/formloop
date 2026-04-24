"""End-to-end persistence with real cad-cli outputs.

REQ: FLH-F-011, FLH-F-022, FLH-D-023, FLH-D-024
"""

from __future__ import annotations

from pathlib import Path

import pytest

from formloop.runtime.cad_cli import cad_build, cad_inspect_summary, cad_render
from formloop.schemas import (
    EffectiveRuntime,
    ReviewDecision,
    ReviewSummary,
    RevisionTrigger,
)
from formloop.store import RunStore
from formloop.store.run_store import CandidateBundle

pytestmark = pytest.mark.integration


def test_persist_revision_from_real_cad(
    require_cad_cli: None,
    require_blender: None,
    cube_model: Path,
    tmp_path: Path,
) -> None:
    build = cad_build(model_path=cube_model, output_dir=tmp_path / "build", overrides={"size": 16})
    render = cad_render(glb_path=build.glb_path, output_dir=tmp_path / "render")
    inspect = cad_inspect_summary(build.step_path)
    inspect_json = tmp_path / "inspect.json"
    inspect_json.write_text(inspect.model_dump_json(indent=2))

    # Stage views-only directory (cad render emits views + sheet flat in output_dir).
    views_staging = tmp_path / "views_staging"
    views_staging.mkdir()
    for view_path in render.view_paths():
        if view_path.is_file():
            (views_staging / view_path.name).write_bytes(view_path.read_bytes())

    build_out = Path(build.output_dir)
    render_out = Path(render.output_dir)
    build_meta = build_out / "build-metadata.json"
    render_meta = render_out / "render-metadata.json"

    store = RunStore(runs_root=tmp_path / "runs")
    run, layout = store.create_run(
        input_summary="a 16mm cube",
        effective_runtime=EffectiveRuntime(
            profile="dev_test", model="gpt-5.4-nano", reasoning="low"
        ),
    )

    bundle = CandidateBundle(
        trigger=RevisionTrigger.initial,
        spec_snapshot={"kind": "cube", "size": 16},
        designer_notes="Used cube.py with size=16.",
        known_risks=[],
        model_py_src=cube_model,
        step_src=build.step_path,
        glb_src=build.glb_path,
        views_dir_src=views_staging,
        render_sheet_src=render.sheet_path,
        build_metadata_src=build_meta if build_meta.is_file() else None,
        render_metadata_src=render_meta if render_meta.is_file() else None,
        inspect_summary_src=inspect_json,
    )
    revision, rev_layout = store.persist_revision(run, bundle)

    assert rev_layout.model_py.is_file() and rev_layout.model_py.stat().st_size > 0
    assert rev_layout.model_py.read_bytes() == cube_model.read_bytes()
    assert rev_layout.step.is_file() and rev_layout.step.stat().st_size > 0
    assert rev_layout.glb.is_file() and rev_layout.glb.stat().st_size > 0
    assert rev_layout.render_sheet.is_file()
    assert rev_layout.revision_json.is_file()
    assert rev_layout.artifact_manifest.is_file()
    assert rev_layout.inspect_summary.is_file()
    views = sorted(rev_layout.views_dir.glob("*.png"))
    assert len(views) >= 4, f"expected multiple rendered views, got {len(views)}"

    # Attach review and verify snapshot reflects decision.
    review = ReviewSummary(
        decision=ReviewDecision.pass_,
        confidence=0.95,
        key_findings=["Cube matches request."],
    )
    store.attach_review(run, revision.revision_name, review)
    snap = store.load_snapshot(run.run_name)
    assert snap.latest_review_decision == ReviewDecision.pass_
    assert snap.artifacts is not None
    assert snap.artifacts.step_path is not None
    assert snap.artifacts.render_sheet_path is not None
    assert len(snap.artifacts.view_paths) == len(views)
