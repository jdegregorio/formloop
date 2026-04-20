"""Environment loading.

REQ: FLH-D-015, FLH-D-016
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def repo_root() -> Path:
    """Walk up from this file to the repo root (the folder holding pyproject.toml)."""

    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise RuntimeError("could not locate formloop repo root")


def load_env_local() -> None:
    """Load ``.env.local`` from the repo root if present.

    Idempotent. Never overrides variables that are already set in the
    environment. Only logs a debug message when absent.
    """

    path = repo_root() / ".env.local"
    if path.is_file():
        load_dotenv(path, override=False)


def require_openai_key() -> str:
    """Return the OpenAI API key or raise a clear error.

    REQ: FLH-D-016
    """

    load_env_local()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Put it in .env.local at the repo root or "
            "export it in your shell before running formloop."
        )
    return key
