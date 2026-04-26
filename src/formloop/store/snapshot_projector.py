"""Snapshot projection collaborator for polling clients.

REQ: FLH-NF-006
"""

from __future__ import annotations

from ..schemas import ProgressEvent, ReviewSummary, Run, RunSnapshot, RunStatus, SnapshotArtifacts
from .layout import RunLayout


class SnapshotProjector:
    """Derive ``RunSnapshot`` from run state + latest event/review data."""

    def project(
        self,
        run: Run,
        layout: RunLayout,
        *,
        last_event: ProgressEvent | None = None,
        latest_narration: ProgressEvent | None = None,
    ) -> RunSnapshot:
        snap = RunSnapshot(
            run_id=run.run_id,
            run_name=run.run_name,
            status=run.status.value if isinstance(run.status, RunStatus) else str(run.status),
            current_spec=run.current_spec,
            current_revision_name=run.current_revision_id,
            revisions=list(run.revisions),
            research_findings=run.research_findings,
        )
        if run.current_revision_id:
            rev_layout = layout.revision(run.current_revision_id)
            snap.artifacts = SnapshotArtifacts(
                step_path=str(rev_layout.step) if rev_layout.step.is_file() else None,
                glb_path=str(rev_layout.glb) if rev_layout.glb.is_file() else None,
                render_sheet_path=str(rev_layout.render_sheet)
                if rev_layout.render_sheet.is_file()
                else None,
                view_paths=[str(p) for p in sorted(rev_layout.views_dir.glob("*.png"))],
            )
            if rev_layout.review_summary.is_file():
                try:
                    rs = ReviewSummary.model_validate_json(rev_layout.review_summary.read_text())
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

        if latest_narration is not None:
            snap.latest_narration = latest_narration.message
            snap.latest_narration_phase = latest_narration.phase
            snap.latest_narration_index = latest_narration.index

        return snap
