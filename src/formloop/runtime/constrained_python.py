"""Agent-authored Python source handling.

REQ: FLH-D-004

The harness never ``exec()``s Python produced by an agent. Agent-authored
build123d source code is written to disk with :func:`write_model_source` and
is subsequently loaded only by ``cad build``, which has its own bounded
``build_model(params, context) -> build123d.Shape`` contract and its own
process-level isolation. That keeps the blast radius of model code within
cad-cli's existing validation surface.
"""

from __future__ import annotations

from pathlib import Path

from .artifacts import write_artifact


def write_model_source(dest_dir: Path, source: str, filename: str = "model.py") -> Path:
    """Persist agent-authored build123d source and return its absolute path."""

    return write_artifact(dest_dir, filename, source)
