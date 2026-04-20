"""Centralized runtime abstraction.

REQ: FLH-D-004, FLH-D-005, FLH-D-020

The runtime boundary is intentionally small:

- :mod:`formloop.runtime.subprocess` runs external CLI commands.
- :mod:`formloop.runtime.cad_cli` wraps the ``cad`` CLI with typed results.
- :mod:`formloop.runtime.artifacts` handles safe artifact reads/writes.
- :mod:`formloop.runtime.constrained_python` handles agent-authored Python.
"""

from .artifacts import read_artifact, write_artifact
from .cad_cli import (
    CadBuildResult,
    CadCompareResult,
    CadInspectResult,
    CadPackageResult,
    CadRenderResult,
    cad_build,
    cad_compare,
    cad_inspect_bbox,
    cad_inspect_holes,
    cad_inspect_summary,
    cad_inspect_volume,
    cad_package,
    cad_render,
    locate_blender,
    locate_cad,
)
from .constrained_python import write_model_source
from .subprocess import CliError, CliResult, run_cli

__all__ = [
    "CadBuildResult",
    "CadCompareResult",
    "CadInspectResult",
    "CadPackageResult",
    "CadRenderResult",
    "CliError",
    "CliResult",
    "cad_build",
    "cad_compare",
    "cad_inspect_bbox",
    "cad_inspect_holes",
    "cad_inspect_summary",
    "cad_inspect_volume",
    "cad_package",
    "cad_render",
    "locate_blender",
    "locate_cad",
    "read_artifact",
    "run_cli",
    "write_artifact",
    "write_model_source",
]
