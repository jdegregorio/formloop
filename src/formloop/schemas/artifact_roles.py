"""Canonical artifact role registry and resolution helpers.

REQ: FLH-D-022, FLH-D-024, FLH-F-009, FLH-F-025
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_VIEW_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")


@dataclass(frozen=True)
class ArtifactRoleSpec:
    """Canonical contract for an artifact role."""

    role: str
    filename: str
    format: str
    required: bool = True
    persisted_in_manifest: bool = True


_CANONICAL_SPECS: dict[str, ArtifactRoleSpec] = {
    "model_py": ArtifactRoleSpec("model_py", "model.py", "python"),
    "step": ArtifactRoleSpec("step", "step.step", "step"),
    "glb": ArtifactRoleSpec("glb", "model.glb", "glb"),
    "render_sheet": ArtifactRoleSpec("render_sheet", "render-sheet.png", "png"),
    "build_metadata": ArtifactRoleSpec(
        "build_metadata",
        "build-metadata.json",
        "json",
        required=False,
    ),
    "render_metadata": ArtifactRoleSpec(
        "render_metadata",
        "render-metadata.json",
        "json",
        required=False,
    ),
    "inspect_summary": ArtifactRoleSpec(
        "inspect_summary",
        "inspect-summary.json",
        "json",
        required=False,
    ),
    # API-only roles (not emitted into artifact-manifest entries).
    "revision": ArtifactRoleSpec(
        "revision",
        "revision.json",
        "json",
        persisted_in_manifest=False,
    ),
    "manifest": ArtifactRoleSpec(
        "manifest",
        "artifact-manifest.json",
        "json",
        persisted_in_manifest=False,
    ),
    "review": ArtifactRoleSpec(
        "review",
        "review-summary.json",
        "json",
        required=False,
        persisted_in_manifest=False,
    ),
    "designer_notes": ArtifactRoleSpec(
        "designer_notes",
        "designer-notes.md",
        "markdown",
        required=False,
        persisted_in_manifest=False,
    ),
}


def canonical_role_specs() -> tuple[ArtifactRoleSpec, ...]:
    return tuple(_CANONICAL_SPECS.values())


def persisted_manifest_specs() -> tuple[ArtifactRoleSpec, ...]:
    return tuple(spec for spec in _CANONICAL_SPECS.values() if spec.persisted_in_manifest)


def view_role_name(view_stem: str) -> str:
    """Compute a canonical view role (e.g., ``front`` -> ``view_front``)."""

    return f"view_{view_stem}"


def _view_stem_from_role(role: str) -> str | None:
    if not role.startswith("view_"):
        return None
    stem = role.removeprefix("view_")
    if not stem or not _VIEW_NAME_RE.fullmatch(stem):
        return None
    return stem


def is_valid_role_name(role: str) -> bool:
    if role in _CANONICAL_SPECS:
        return True
    return _view_stem_from_role(role) is not None


def resolve_relative_path(role: str) -> str | None:
    """Resolve role to revision-relative path, if recognized."""

    spec = _CANONICAL_SPECS.get(role)
    if spec is not None:
        return spec.filename
    stem = _view_stem_from_role(role)
    if stem is None:
        return None
    return f"views/{stem}.png"


def resolve_format(role: str) -> str | None:
    spec = _CANONICAL_SPECS.get(role)
    if spec is not None:
        return spec.format
    if _view_stem_from_role(role) is not None:
        return "png"
    return None
