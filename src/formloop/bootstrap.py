"""Environment/bootstrap helpers."""

from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv

from .paths import repo_root


@lru_cache(maxsize=1)
def bootstrap_environment() -> None:
    """Load repo-local environment variables once per process."""
    # Req: FLH-D-015, FLH-D-016
    load_dotenv(repo_root() / ".env.local", override=False)
