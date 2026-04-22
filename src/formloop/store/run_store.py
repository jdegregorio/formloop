"""Run and revision persistence.

REQ: FLH-F-009, FLH-F-011, FLH-F-021, FLH-F-022, FLH-F-024, FLH-D-023, FLH-D-024,
REQ: FLH-NF-002, FLH-NF-006, FLH-NF-007
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..schemas import (
    ArtifactEntry,
    ArtifactManifest,
    EffectiveRuntime,
    ProgressEvent,
    ProgressEventKind,
    ReviewSummary,
    Revision,
    RevisionTrigger,
    Run,
    RunSnapshot,
    RunStatus,
    SnapshotArtifacts,
)
from ..schemas._common import utcnow_iso
from .layout import RevisionLayout, RunLayout
from .naming import next_revision_name, next_run_name


def _atomic_write_text(path: Path, text: str) -> None:
    """Atomic write via tmp file + os.replace, creating parent dirs."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_append_line(path: Path, line: str) -> None:
    """Append a single line atomically. Uses flock-free best effort.

    JSONL writes are short enough that POSIX O_APPEND on local disks is
    effectively atomic for a single write.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip("\n") + "\n")


@dataclass
class CandidateBundle:
    """Inputs used to persist a revision."""

    trigger: RevisionTrigger
    spec_snapshot: dict[str, Any]
    designer_notes: str | None
    known_risks: list[str]
    model_py_src: Path
    step_src: Path
    glb_src: Path
    views_dir_src: Path
    render_sheet_src: Path
    build_metadata_src: Path | None = None
    render_metadata_src: Path | None = None
    inspect_summary_src: Path | None = None


class RunStore:
    """Create, load, and mutate persisted runs."""

    def __init__(self, runs_root: Path) -> None:
        self.runs_root = runs_root
        self.runs_root.mkdir(parents=True, exist_ok=True)

    # ---- run lifecycle ----------------------------------------------------

    def create_run(
        self,
        *,
        input_summary: str,
        effective_runtime: EffectiveRuntime,
        reference_image: str | None = None,
    ) -> tuple[Run, RunLayout]:
        """Allocate a fresh run directory + Run record."""

        name = next_run_name(self.runs_root)
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
        layout = RunLayout(runs_root=self.runs_root, run_name=run.run_name)
        _atomic_write_text(layout.run_json, run.model_dump_json(indent=2))
        self._refresh_snapshot(run, layout)

    def load_run(self, run_name: str) -> Run:
        layout = RunLayout(runs_root=self.runs_root, run_name=run_name)
        return Run.model_validate_json(layout.run_json.read_text())

    def layout(self, run_name: str) -> RunLayout:
        return RunLayout(runs_root=self.runs_root, run_name=run_name)

    # ---- events -----------------------------------------------------------

    def _next_event_index(self, layout: RunLayout) -> int:
        if not layout.events_jsonl.is_file():
            return 0
        with layout.events_jsonl.open("rb") as fh:
            try:
                fh.seek(-2, os.SEEK_END)
            except OSError:
                fh.seek(0)
            while fh.read(1) != b"\n":
                if fh.tell() <= 1:
                    fh.seek(0)
                    break
                fh.seek(-2, os.SEEK_CUR)
            last = fh.readline().decode("utf-8").strip()
        if not last:
            # count lines fallback
            with layout.events_jsonl.open() as fh:
                return sum(1 for _ in fh)
        try:
            return int(json.loads(last)["index"]) + 1
        except Exception:
            with layout.events_jsonl.open() as fh:
                return sum(1 for _ in fh)

    def append_event(self, run_name: str, event: ProgressEvent) -> ProgressEvent:
        layout = self.layout(run_name)
        if event.index == 0 and layout.events_jsonl.is_file():
            # Auto-assign an index when caller passed a zero placeholder.
            event = event.model_copy(update={"index": self._next_event_index(layout)})
        _atomic_append_line(layout.events_jsonl, event.model_dump_json())
        # Refresh snapshot lightly (reading the whole run.json can be heavy
        # but the runs are small enough that this is fine).
        if layout.run_json.is_file():
            run = self.load_run(run_name)
            self._refresh_snapshot(run, layout, last_event=event)
        return event

    def read_events(self, run_name: str, *, since: int = 0) -> list[ProgressEvent]:
        layout = self.layout(run_name)
        if not layout.events_jsonl.is_file():
            return []
        events: list[ProgressEvent] = []
        with layout.events_jsonl.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                ev = ProgressEvent.model_validate_json(line)
                if ev.index >= since:
                    events.append(ev)
        return events

    # ---- revisions --------------------------------------------------------

    def persist_revision(
        self, run: Run, bundle: CandidateBundle
    ) -> tuple[Revision, RevisionLayout]:
        """Copy a candidate artifact bundle into the run and record a Revision.

        A Revision exists only after this returns successfully (FLH-F-022).
        """

        layout = RunLayout(runs_root=self.runs_root, run_name=run.run_name)
        name = next_revision_name(layout.revisions_dir)
        ordinal = len(run.revisions) + 1
        rev_layout = layout.revision(name)
        rev_layout.root.mkdir(parents=True, exist_ok=True)
        rev_layout.views_dir.mkdir(parents=True, exist_ok=True)

        # Copy core artifacts.
        self._copy_file(bundle.model_py_src, rev_layout.model_py)
        self._copy_file(bundle.step_src, rev_layout.step)
        self._copy_file(bundle.glb_src, rev_layout.glb)
        self._copy_file(bundle.render_sheet_src, rev_layout.render_sheet)
        for view in sorted(bundle.views_dir_src.glob("*.png")):
            self._copy_file(view, rev_layout.views_dir / view.name)

        # Optional metadata carries traceability (FLH-NF-002).
        if bundle.build_metadata_src is not None:
            self._copy_file(bundle.build_metadata_src, rev_layout.build_meta)
        if bundle.render_metadata_src is not None:
            self._copy_file(bundle.render_metadata_src, rev_layout.render_meta)
        if bundle.inspect_summary_src is not None:
            self._copy_file(bundle.inspect_summary_src, rev_layout.inspect_summary)

        # Designer notes if provided.
        if bundle.designer_notes:
            rev_layout.designer_notes.write_text(bundle.designer_notes, encoding="utf-8")

        # Build the manifest.
        entries: list[ArtifactEntry] = [
            ArtifactEntry(role="model_py", path="model.py", format="python"),
            ArtifactEntry(role="step", path="step.step", format="step"),
            ArtifactEntry(role="glb", path="model.glb", format="glb"),
            ArtifactEntry(role="render_sheet", path="render-sheet.png", format="png"),
        ]
        for view in sorted(rev_layout.views_dir.glob("*.png")):
            entries.append(
                ArtifactEntry(
                    role=f"view_{view.stem}",
                    path=f"views/{view.name}",
                    format="png",
                )
            )
        if rev_layout.build_meta.is_file():
            entries.append(
                ArtifactEntry(
                    role="build_metadata",
                    path="build-metadata.json",
                    format="json",
                    required=False,
                )
            )
        if rev_layout.render_meta.is_file():
            entries.append(
                ArtifactEntry(
                    role="render_metadata",
                    path="render-metadata.json",
                    format="json",
                    required=False,
                )
            )
        if rev_layout.inspect_summary.is_file():
            entries.append(
                ArtifactEntry(
                    role="inspect_summary",
                    path="inspect-summary.json",
                    format="json",
                    required=False,
                )
            )
        manifest = ArtifactManifest(revision_name=name, entries=entries)
        _atomic_write_text(
            rev_layout.artifact_manifest, manifest.model_dump_json(indent=2)
        )

        # Revision record.
        revision = Revision(
            revision_id=str(uuid.uuid4()),
            revision_name=name,
            ordinal=ordinal,
            trigger=bundle.trigger,
            spec_snapshot=bundle.spec_snapshot,
            designer_notes=bundle.designer_notes,
            known_risks=bundle.known_risks,
            artifact_manifest_path=str(
                rev_layout.artifact_manifest.relative_to(layout.root)
            ),
        )
        _atomic_write_text(rev_layout.revision_json, revision.model_dump_json(indent=2))

        # Update the run.
        run.revisions.append(name)
        run.current_revision_id = name
        self.save_run(run)

        return revision, rev_layout

    def attach_review(
        self, run: Run, revision_name: str, review: ReviewSummary
    ) -> Path:
        """Write review-summary.json next to the revision and update pointers."""

        layout = RunLayout(runs_root=self.runs_root, run_name=run.run_name)
        rev_layout = layout.revision(revision_name)
        _atomic_write_text(rev_layout.review_summary, review.model_dump_json(indent=2))

        # Patch revision.json to record the review path.
        revision = Revision.model_validate_json(rev_layout.revision_json.read_text())
        revision.review_summary_path = str(
            rev_layout.review_summary.relative_to(layout.root)
        )
        _atomic_write_text(rev_layout.revision_json, revision.model_dump_json(indent=2))

        # Refresh snapshot so pollers see the decision immediately.
        self._refresh_snapshot(run, layout)
        return rev_layout.review_summary

    # ---- snapshot ---------------------------------------------------------

    def _refresh_snapshot(
        self,
        run: Run,
        layout: RunLayout,
        *,
        last_event: ProgressEvent | None = None,
    ) -> RunSnapshot:
        snap = RunSnapshot(
            run_id=run.run_id,
            run_name=run.run_name,
            status=run.status.value if isinstance(run.status, RunStatus) else str(run.status),
            current_spec=run.current_spec,
            current_revision_name=run.current_revision_id,
            revisions=list(run.revisions),
        )
        # Artifact pointers from the current revision, if any.
        if run.current_revision_id:
            rev_layout = layout.revision(run.current_revision_id)
            arts = SnapshotArtifacts(
                step_path=str(rev_layout.step) if rev_layout.step.is_file() else None,
                glb_path=str(rev_layout.glb) if rev_layout.glb.is_file() else None,
                render_sheet_path=(
                    str(rev_layout.render_sheet)
                    if rev_layout.render_sheet.is_file()
                    else None
                ),
                view_paths=[
                    str(p) for p in sorted(rev_layout.views_dir.glob("*.png"))
                ],
            )
            snap.artifacts = arts
            if rev_layout.review_summary.is_file():
                try:
                    rs = ReviewSummary.model_validate_json(
                        rev_layout.review_summary.read_text()
                    )
                    snap.latest_review_decision = rs.decision
                    snap.latest_review_summary_path = str(
                        rev_layout.review_summary.relative_to(layout.root)
                    )
                except Exception:
                    pass

        if last_event is not None:
            snap.last_event_index = last_event.index
            snap.last_event_kind = last_event.kind.value
            snap.last_message = last_event.message

        # Surface the most recent narration event so polling clients
        # (UI + CLI) can show the live reasoning-trace line without having
        # to rescan the events file themselves.
        latest_narration = self._find_latest_narration(layout, last_event)
        if latest_narration is not None:
            snap.latest_narration = latest_narration.message
            snap.latest_narration_phase = latest_narration.phase
            snap.latest_narration_index = latest_narration.index

        _atomic_write_text(layout.snapshot_json, snap.model_dump_json(indent=2))
        return snap

    def _find_latest_narration(
        self, layout: RunLayout, last_event: ProgressEvent | None
    ) -> ProgressEvent | None:
        """Return the most recent narration event, or ``None``."""

        if (
            last_event is not None
            and last_event.kind is ProgressEventKind.narration
        ):
            return last_event
        if not layout.events_jsonl.is_file():
            return None
        latest: ProgressEvent | None = None
        with layout.events_jsonl.open() as fh:
            for line in fh:
                line = line.strip()
                if not line or '"narration"' not in line:
                    continue
                try:
                    ev = ProgressEvent.model_validate_json(line)
                except Exception:
                    continue
                if ev.kind is ProgressEventKind.narration:
                    latest = ev
        return latest

    def load_snapshot(self, run_name: str) -> RunSnapshot:
        layout = self.layout(run_name)
        return RunSnapshot.model_validate_json(layout.snapshot_json.read_text())

    # ---- helpers ----------------------------------------------------------

    @staticmethod
    def _copy_file(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
