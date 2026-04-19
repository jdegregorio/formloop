"""Path helpers for the Formloop repository."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def src_root() -> Path:
    return repo_root() / "src"


def schema_root() -> Path:
    return repo_root() / "schemas"


def dataset_root() -> Path:
    return repo_root() / "datasets"


def runtime_root() -> Path:
    return repo_root() / "var" / "runs"


def sibling_cad_cli_root() -> Path:
    return repo_root().parent / "cad-cli"
