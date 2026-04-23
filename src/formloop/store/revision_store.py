"""Revision artifact persistence collaborator.

REQ: FLH-F-022, FLH-D-024, FLH-NF-002
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ..schemas import ArtifactEntry, ArtifactManifest, Revision, Run
from .io import atomic_write_text
from .layout import RevisionLayout, RunLayout
from .naming import next_revision_name
from .candidate_bundle import CandidateBundle


class RevisionStore:
    """Copy artifact bundles and write revision records."""

    def persist(self, run: Run, layout: RunLayout, bundle: CandidateBundle) -> tuple[Revision, RevisionLayout]:
        name = next_revision_name(layout.revisions_dir)
        ordinal = len(run.revisions) + 1
        rev_layout = layout.revision(name)
        rev_layout.root.mkdir(parents=True, exist_ok=True)
        rev_layout.views_dir.mkdir(parents=True, exist_ok=True)

        self._copy_file(bundle.model_py_src, rev_layout.model_py)
        self._copy_file(bundle.step_src, rev_layout.step)
        self._copy_file(bundle.glb_src, rev_layout.glb)
        self._copy_file(bundle.render_sheet_src, rev_layout.render_sheet)
        for view in sorted(bundle.views_dir_src.glob("*.png")):
            self._copy_file(view, rev_layout.views_dir / view.name)

        if bundle.build_metadata_src is not None:
            self._copy_file(bundle.build_metadata_src, rev_layout.build_meta)
        if bundle.render_metadata_src is not None:
            self._copy_file(bundle.render_metadata_src, rev_layout.render_meta)
        if bundle.inspect_summary_src is not None:
            self._copy_file(bundle.inspect_summary_src, rev_layout.inspect_summary)

        if bundle.designer_notes:
            rev_layout.designer_notes.write_text(bundle.designer_notes, encoding="utf-8")

        manifest = ArtifactManifest(
            revision_name=name,
            entries=self._manifest_entries(rev_layout),
        )
        atomic_write_text(rev_layout.artifact_manifest, manifest.model_dump_json(indent=2))

        revision = Revision(
            revision_id=str(uuid.uuid4()),
            revision_name=name,
            ordinal=ordinal,
            trigger=bundle.trigger,
            spec_snapshot=bundle.spec_snapshot,
            designer_notes=bundle.designer_notes,
            known_risks=bundle.known_risks,
            artifact_manifest_path=str(rev_layout.artifact_manifest.relative_to(layout.root)),
        )
        atomic_write_text(rev_layout.revision_json, revision.model_dump_json(indent=2))
        return revision, rev_layout

    def attach_review_path(self, layout: RunLayout, revision_name: str, review_json: str) -> Path:
        rev_layout = layout.revision(revision_name)
        atomic_write_text(rev_layout.review_summary, review_json)

        revision = Revision.model_validate_json(rev_layout.revision_json.read_text())
        revision.review_summary_path = str(rev_layout.review_summary.relative_to(layout.root))
        atomic_write_text(rev_layout.revision_json, revision.model_dump_json(indent=2))
        return rev_layout.review_summary

    @staticmethod
    def _manifest_entries(rev_layout: RevisionLayout) -> list[ArtifactEntry]:
        entries: list[ArtifactEntry] = [
            ArtifactEntry(role="model_py", path="model.py", format="python"),
            ArtifactEntry(role="step", path="model.step", format="step"),
            ArtifactEntry(role="glb", path="model.glb", format="glb"),
            ArtifactEntry(role="render_sheet", path="render-sheet.png", format="png"),
        ]
        for view in sorted(rev_layout.views_dir.glob("*.png")):
            entries.append(ArtifactEntry(role=f"view_{view.stem}", path=f"views/{view.name}", format="png"))
        if rev_layout.build_meta.is_file():
            entries.append(ArtifactEntry(role="build_metadata", path="build-metadata.json", format="json", required=False))
        if rev_layout.render_meta.is_file():
            entries.append(ArtifactEntry(role="render_metadata", path="render-metadata.json", format="json", required=False))
        if rev_layout.inspect_summary.is_file():
            entries.append(ArtifactEntry(role="inspect_summary", path="inspect-summary.json", format="json", required=False))
        return entries

    @staticmethod
    def _copy_file(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
