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
    CadRenderResult,
    cad_build,
    cad_compare,
    cad_inspect_summary,
    cad_render,
    locate_blender,
    locate_cad,
)
from .constrained_python import write_model_source
from .multimodal import image_file_to_input_image, text_and_image_list_to_sdk_message_payload
from .subprocess import CliError, CliResult, run_cli

__all__ = [
    "CadBuildResult",
    "CadCompareResult",
    "CadInspectResult",
    "CadRenderResult",
    "CliError",
    "CliResult",
    "cad_build",
    "cad_compare",
    "cad_inspect_summary",
    "cad_render",
    "locate_blender",
    "locate_cad",
    "image_file_to_input_image",
    "read_artifact",
    "text_and_image_list_to_sdk_message_payload",
    "run_cli",
    "write_artifact",
    "write_model_source",
]
