"""Shared ANSI + terminal-width helpers for the Formloop CLI.

Keeps a single source of truth for colour codes and TTY detection so the
live ``EventRenderer`` and the static header/footer formatter agree on what
a "rich" terminal means.
"""

from __future__ import annotations

import os
import shutil
from typing import IO

RESET = "\x1b[0m"
DIM = "\x1b[2m"
BOLD = "\x1b[1m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
CYAN = "\x1b[36m"


def supports_ansi(stream: IO[str]) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty"):
        return False
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def terminal_width(
    *,
    default: int = 100,
    min_width: int = 40,
    max_width: int | None = None,
) -> int:
    try:
        columns = shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default
    if max_width is not None:
        columns = min(max_width, columns)
    return max(min_width, columns)
