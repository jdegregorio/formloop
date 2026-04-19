from __future__ import annotations

from formloop.models import NormalizedSpec, ProgressEvent, RunCreateRequest
from formloop.persistence import RunStore


def test_flh_f_021_through_flh_d_023_run_and_revision_layout(tmp_path) -> None:
    store = RunStore(tmp_path / "runs")
    run = store.create_run(
        RunCreateRequest(prompt="make a cube"),
        input_summary="cube",
        current_spec=NormalizedSpec(intent_summary="cube"),
        effective_profile="dev_test",
        effective_model="gpt-5.4-nano",
        effective_reasoning="low",
    )
    revision, revision_dir = store.create_revision(run=run, trigger="initial_design")
    assert run.run_name == "run-000001"
    assert revision.revision_name == "rev-001"
    assert revision_dir.exists()
    assert (store.run_dir(run.run_name) / "run.json").exists()
    assert (revision_dir / "views").exists()


def test_flh_f_024_progress_events_are_append_only(tmp_path) -> None:
    store = RunStore(tmp_path / "runs")
    run = store.create_run(
        RunCreateRequest(prompt="make a cube"),
        input_summary="cube",
        current_spec=NormalizedSpec(intent_summary="cube"),
        effective_profile="dev_test",
        effective_model="gpt-5.4-nano",
        effective_reasoning="low",
    )
    event = ProgressEvent(
        event_id="evt-1",
        event_type="run_created",
        status="ok",
        breadcrumb="Run created",
    )
    store.append_event(run.run_name, event)
    events = store.list_events(run.run_name)
    assert len(events) == 1
    assert events[0].breadcrumb == "Run created"
