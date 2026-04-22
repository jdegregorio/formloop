"""Filesystem layout for runs and revisions.

REQ: FLH-D-023, FLH-D-024
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RevisionLayout:
    """Paths inside a single revision bundle."""

    root: Path

    @property
    def revision_json(self) -> Path:
        return self.root / "revision.json"

    @property
    def artifact_manifest(self) -> Path:
        return self.root / "artifact-manifest.json"

    @property
    def step(self) -> Path:
        return self.root / "step.step"

    @property
    def glb(self) -> Path:
        return self.root / "model.glb"

    @property
    def model_py(self) -> Path:
        return self.root / "model.py"

    @property
    def render_sheet(self) -> Path:
        return self.root / "render-sheet.png"

    @property
    def views_dir(self) -> Path:
        return self.root / "views"

    @property
    def review_summary(self) -> Path:
        return self.root / "review-summary.json"

    @property
    def build_meta(self) -> Path:
        return self.root / "build-metadata.json"

    @property
    def render_meta(self) -> Path:
        return self.root / "render-metadata.json"

    @property
    def inspect_summary(self) -> Path:
        return self.root / "inspect-summary.json"

    @property
    def designer_notes(self) -> Path:
        return self.root / "designer-notes.md"


@dataclass(frozen=True, slots=True)
class RunLayout:
    """Paths inside one run folder."""

    runs_root: Path
    run_name: str

    @property
    def root(self) -> Path:
        return self.runs_root / self.run_name

    @property
    def run_json(self) -> Path:
        return self.root / "run.json"

    @property
    def events_jsonl(self) -> Path:
        return self.root / "events.jsonl"

    @property
    def snapshot_json(self) -> Path:
        return self.root / "snapshot.json"

    @property
    def revisions_dir(self) -> Path:
        return self.root / "revisions"

    def revision(self, name: str) -> RevisionLayout:
        return RevisionLayout(root=self.revisions_dir / name)

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.revisions_dir.mkdir(parents=True, exist_ok=True)
