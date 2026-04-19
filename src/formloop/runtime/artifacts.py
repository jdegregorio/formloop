"""Safe artifact I/O.

REQ: FLH-D-004, FLH-NF-002

Every read/write is validated to stay inside an allowed root so agent tools
cannot accidentally reach beyond a run's own folder.
"""

from __future__ import annotations

from pathlib import Path


class ArtifactPathError(RuntimeError):
    """Raised when an artifact path escapes the allowed root."""


def _ensure_under(root: Path, target: Path) -> Path:
    root_r = root.resolve()
    target_r = target.resolve() if target.is_absolute() else (root_r / target).resolve()
    try:
        target_r.relative_to(root_r)
    except ValueError as exc:
        raise ArtifactPathError(
            f"path {target_r} escapes allowed root {root_r}"
        ) from exc
    return target_r


def write_artifact(root: Path, relative: Path | str, content: bytes | str) -> Path:
    """Write ``content`` to ``root/relative``. Creates parent dirs.

    Raises :class:`ArtifactPathError` if ``relative`` resolves outside ``root``.
    """

    target = _ensure_under(root, Path(relative))
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        target.write_text(content, encoding="utf-8")
    else:
        target.write_bytes(content)
    return target


def read_artifact(root: Path, relative: Path | str, *, binary: bool = False) -> bytes | str:
    """Read ``root/relative`` safely, enforcing the root-scope invariant."""

    target = _ensure_under(root, Path(relative))
    if not target.is_file():
        raise FileNotFoundError(target)
    if binary:
        return target.read_bytes()
    return target.read_text(encoding="utf-8")
