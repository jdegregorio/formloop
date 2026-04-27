"""Run and revision persistence facade.

REQ: FLH-F-009, FLH-F-011, FLH-F-021, FLH-F-022, FLH-F-024, FLH-D-023, FLH-D-024,
REQ: FLH-NF-002, FLH-NF-006, FLH-NF-007
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ..schemas import (
    EffectiveRuntime,
    ProgressEvent,
    ProgressEventKind,
    ReviewSummary,
    Run,
    RunSnapshot,
)
from ..schemas._common import utcnow_iso
from .candidate_bundle import CandidateBundle
from .event_log import EventLog
from .io import atomic_write_text
from .layout import RunLayout
from .naming import reserve_next_run_name_dir
from .revision_store import RevisionStore
from .snapshot_projector import SnapshotProjector


class RunStore:
    """Create, load, and mutate persisted runs.

    This class is intentionally a thin compatibility facade that delegates
    focused concerns to collaborators:
    - ``EventLog`` for events.jsonl behavior
    - ``RevisionStore`` for revision artifact persistence
    - ``SnapshotProjector`` for run snapshot projection
    """

    def __init__(self, runs_root: Path) -> None:
        self.runs_root = runs_root
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self._events = EventLog()
        self._revisions = RevisionStore()
        self._snapshots = SnapshotProjector()

    def create_run(
        self,
        *,
        input_summary: str,
        effective_runtime: EffectiveRuntime,
        reference_image: str | None = None,
    ) -> tuple[Run, RunLayout]:
        name = reserve_next_run_name_dir(self.runs_root)
        layout = RunLayout(runs_root=self.runs_root, run_name=name)
        layout.ensure()

        run = Run(
            run_id=str(uuid.uuid4()),
            run_name=name,
            input_summary=input_summary,
            reference_image=reference_image,
            effective_runtime=effective_runtime,
        )
        self.save_run(run)
        self.append_event(
            name,
            ProgressEvent(
                index=0,
                kind=ProgressEventKind.run_created,
                message=f"run {name} created",
                data={"input_summary": input_summary},
            ),
        )
        return run, layout

    def save_run(self, run: Run) -> None:
        run.updated_at = utcnow_iso()
        layout = self.layout(run.run_name)
        atomic_write_text(layout.run_json, run.model_dump_json(indent=2))
        self._refresh_snapshot(run, layout)

    def load_run(self, run_name: str) -> Run:
        return Run.model_validate_json(self.layout(run_name).run_json.read_text())

    def layout(self, run_name: str) -> RunLayout:
        return RunLayout(runs_root=self.runs_root, run_name=run_name)

    def append_event(self, run_name: str, event: ProgressEvent) -> ProgressEvent:
        layout = self.layout(run_name)
        assigned = self._events.append(layout, event)
        if layout.run_json.is_file():
            run = self.load_run(run_name)
            self._refresh_snapshot(run, layout, last_event=assigned)
        return assigned

    def read_events(self, run_name: str, *, since: int = 0) -> list[ProgressEvent]:
        return self._events.read(self.layout(run_name), since=since)

    def persist_revision(self, run: Run, bundle: CandidateBundle):
        layout = self.layout(run.run_name)
        revision, rev_layout = self._revisions.persist(run, layout, bundle)
        run.revisions.append(revision.revision_name)
        run.current_revision_id = revision.revision_name
        self.save_run(run)
        return revision, rev_layout

    def attach_review(self, run: Run, revision_name: str, review: ReviewSummary):
        layout = self.layout(run.run_name)
        path = self._revisions.attach_review_path(
            layout, revision_name, review.model_dump_json(indent=2)
        )
        self._refresh_snapshot(run, layout)
        return path

    def _refresh_snapshot(
        self,
        run: Run,
        layout: RunLayout,
        *,
        last_event: ProgressEvent | None = None,
    ) -> RunSnapshot:
        latest_narration = self._events.find_latest_narration(layout, last_event)
        snap = self._snapshots.project(
            run,
            layout,
            last_event=last_event,
            latest_narration=latest_narration,
        )
        atomic_write_text(layout.snapshot_json, snap.model_dump_json(indent=2))
        return snap

    def load_snapshot(self, run_name: str) -> RunSnapshot:
        return RunSnapshot.model_validate_json(self.layout(run_name).snapshot_json.read_text())
