"""Typed wrappers around the ``cad`` CLI.

REQ: FLH-D-001, FLH-D-002, FLH-D-003, FLH-D-020, FLH-V-007

Every call shells out with ``--format json``, parses the structured stdout,
and returns a Pydantic model that mirrors the cad-cli dataclass contract.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .subprocess import CliError, run_cli

# ---------------------------------------------------------------------------
# Result models — mirror cad_cli.schemas dataclasses.
# ---------------------------------------------------------------------------


class _CadResult(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    schema_version: int = 1
    status: str = "ok"
    command: str
    summary: str


class BoundingBoxRecord(BaseModel):
    model_config = ConfigDict(extra="allow")
    min_corner: list[float]
    max_corner: list[float]
    size: list[float]


class CadBuildResult(_CadResult):
    output_dir: str
    metadata_path: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    bounding_box: BoundingBoxRecord
    volume: float

    @property
    def step_path(self) -> Path:
        return Path(self.output_dir) / "model.step"

    @property
    def glb_path(self) -> Path:
        return Path(self.output_dir) / "model.glb"


class CadRenderResult(_CadResult):
    input_glb: str
    output_dir: str
    metadata_path: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    blender_bin: str
    render_spec: dict[str, Any] = Field(default_factory=dict)

    @property
    def sheet_path(self) -> Path:
        return Path(self.output_dir) / "sheet.png"

    def view_paths(self) -> list[Path]:
        return [
            Path(self.output_dir) / f"{name}.png"
            for name in ("front", "back", "left", "right", "top", "bottom", "iso")
        ]


class CadInspectResult(_CadResult):
    artifact_path: str
    mode: str
    data: dict[str, Any] = Field(default_factory=dict)


class CadCompareMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")
    mode: str
    alignment: str
    left_volume: float | None = None
    right_volume: float | None = None
    shared_volume: float | None = None
    left_only_volume: float | None = None
    right_only_volume: float | None = None
    union_volume: float | None = None
    overlap_ratio: float | None = None
    notes: list[str] = Field(default_factory=list)


class CadCompareResult(_CadResult):
    left_path: str
    right_path: str
    output_dir: str
    metrics_path: str
    metrics: CadCompareMetrics
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool discovery.
# ---------------------------------------------------------------------------


def locate_cad() -> str:
    """Resolve the ``cad`` executable path. Raises CliError if missing.

    Prefers the formloop venv's own ``cad`` script (installed by ``uv sync``
    via the cad-cli pip dependency) over any global ``uv tool install`` shim,
    so the model loaded by ``cad build --python ...`` and the rest of formloop
    share one Python environment.
    """

    venv_local = Path(sys.executable).parent / "cad"
    if venv_local.is_file():
        return str(venv_local)
    path = shutil.which("cad")
    if not path:
        raise CliError(
            cmd=["cad"],
            returncode=127,
            stdout="",
            stderr="",
            message=(
                "`cad` CLI not found. Run `uv sync` to install cad-cli into the "
                "formloop venv, or ensure a `cad` binary is on PATH."
            ),
        )
    return path


def locate_blender(explicit: str | os.PathLike[str] | None = None) -> str | None:
    """Return a best-effort Blender binary path.

    Resolution order: explicit arg → CAD_BLENDER_BIN env → ``blender`` on PATH.
    Returns ``None`` if Blender cannot be resolved (callers decide whether
    that's fatal).
    """

    if explicit:
        return str(explicit)
    env = os.environ.get("CAD_BLENDER_BIN")
    if env:
        return env
    return shutil.which("blender")


# ---------------------------------------------------------------------------
# Helper: convert parameter overrides into --set KEY=JSON-VALUE.
# ---------------------------------------------------------------------------


def _format_overrides(overrides: dict[str, Any] | None) -> list[str]:
    if not overrides:
        return []
    args: list[str] = []
    for key, value in overrides.items():
        args.extend(["--set", f"{key}={json.dumps(value)}"])
    return args


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------


def cad_build(
    *,
    model_path: Path,
    output_dir: Path,
    overrides: dict[str, Any] | None = None,
    timeout: float | None = None,
    python_path: str | os.PathLike[str] | None = None,
) -> CadBuildResult:
    """Invoke ``cad build`` and return the parsed result.

    ``python_path`` is forwarded to ``cad build --python``; defaults to
    ``sys.executable`` so the model is evaluated in the formloop venv. Pass
    ``False``/``""`` explicitly via ``python_path=""`` to use cad-cli's own
    interpreter (the legacy embedded path).
    """

    cmd: list[str] = [
        locate_cad(),
        "build",
        str(model_path),
        "--output-dir",
        str(output_dir),
        "--format",
        "json",
    ]
    if python_path is None:
        python_path = sys.executable
    if python_path:
        cmd += ["--python", str(python_path)]
    cmd += _format_overrides(overrides)
    result = run_cli(cmd, timeout=timeout)
    payload = result.parse_json()
    return CadBuildResult.model_validate(payload)


def cad_render(
    *,
    glb_path: Path,
    output_dir: Path,
    spec_path: Path | None = None,
    blender_bin: str | None = None,
    timeout: float | None = None,
) -> CadRenderResult:
    """Invoke ``cad render`` and return the parsed result."""

    cmd: list[str] = [
        locate_cad(),
        "render",
        str(glb_path),
        "--output-dir",
        str(output_dir),
        "--format",
        "json",
    ]
    if spec_path is not None:
        cmd += ["--spec", str(spec_path)]
    if blender_bin:
        cmd += ["--blender-bin", blender_bin]
    result = run_cli(cmd, timeout=timeout)
    payload = result.parse_json()
    return CadRenderResult.model_validate(payload)


def _cad_inspect(
    subcommand: str, artifact_path: Path, *extra: str, timeout: float | None = None
) -> CadInspectResult:
    cmd: list[str] = [
        locate_cad(),
        "inspect",
        subcommand,
        str(artifact_path),
        *extra,
        "--format",
        "json",
    ]
    result = run_cli(cmd, timeout=timeout)
    payload = result.parse_json()
    return CadInspectResult.model_validate(payload)


def cad_inspect_summary(artifact_path: Path, *, timeout: float | None = None) -> CadInspectResult:
    return _cad_inspect("summary", artifact_path, timeout=timeout)


def cad_compare(
    *,
    left_path: Path,
    right_path: Path,
    output_dir: Path,
    alignment: str = "principal",
    emit_diff_solids: bool = False,
    render_diffs: bool = False,
    blender_bin: str | None = None,
    timeout: float | None = None,
) -> CadCompareResult:
    """Invoke ``cad compare`` for deterministic eval metrics."""

    cmd: list[str] = [
        locate_cad(),
        "compare",
        str(left_path),
        str(right_path),
        "--output-dir",
        str(output_dir),
        "--align",
        alignment,
        "--format",
        "json",
    ]
    if emit_diff_solids:
        cmd += ["--emit-diff-solids"]
    if render_diffs:
        cmd += ["--render-diffs"]
    if blender_bin:
        cmd += ["--blender-bin", blender_bin]
    result = run_cli(cmd, timeout=timeout)
    payload = result.parse_json()
    return CadCompareResult.model_validate(payload)
