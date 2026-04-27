"""File IO helpers for store persistence."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def _default_file_mode() -> int:
    """Return Path.write_text-like create mode (respecting process umask)."""

    umask = os.umask(0)
    os.umask(umask)
    return 0o666 & ~umask


def atomic_write_text(path: Path, text: str) -> None:
    """Atomic write via tmp file + os.replace, creating parent dirs."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    replaced = False
    target_mode = _default_file_mode()
    if path.exists():
        target_mode = stat.S_IMODE(path.stat().st_mode)
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
            prefix=f"{path.name}.",
        ) as tmp:
            temp_path = Path(tmp.name)
            os.fchmod(tmp.fileno(), target_mode)
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())

        os.replace(temp_path, path)
        replaced = True

        if os.name == "posix":
            dir_fd: int | None = None
            try:
                dir_fd = os.open(path.parent, os.O_RDONLY)
                os.fsync(dir_fd)
            except OSError:
                pass
            finally:
                if dir_fd is not None:
                    os.close(dir_fd)
    except Exception:
        if temp_path is not None and not replaced:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
