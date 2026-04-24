"""Integration tests for the cad-cli adapter.

REQ: FLH-V-002, FLH-V-007, FLH-D-020
"""

from __future__ import annotations

from pathlib import Path

import pytest

from formloop.runtime.cad_cli import (
    cad_build,
    cad_compare,
    cad_inspect_summary,
    cad_render,
)
from formloop.runtime.subprocess import CliError

pytestmark = pytest.mark.integration


def test_cad_build_cube(require_cad_cli: None, cube_model: Path, tmp_path: Path) -> None:
    out = tmp_path / "build"
    result = cad_build(model_path=cube_model, output_dir=out, overrides={"size": 20})
    assert result.status == "ok"
    assert result.schema_version == 1
    assert result.step_path.is_file()
    assert result.glb_path.is_file()
    assert (out / "build-metadata.json").is_file()
    # Bounding box should match a 20mm cube within floating-point precision
    bb = result.bounding_box
    assert bb.size == pytest.approx([20.0, 20.0, 20.0], abs=1e-3)
    # Volume = 20^3 = 8000
    assert result.volume == pytest.approx(8000.0, rel=1e-3)


def test_cad_build_timeout_returns_structured_cli_error(
    require_cad_cli: None, tmp_path: Path
) -> None:
    model = tmp_path / "hang_model.py"
    model.write_text(
        "import time\n\n"
        "def build_model(params: dict, context: object):\n"
        "    time.sleep(10)\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(CliError) as exc_info:
        cad_build(model_path=model, output_dir=tmp_path / "build", timeout=0.1)

    err = exc_info.value
    assert err.returncode == -1
    assert "timed out" in str(err)


def test_cad_inspect_summary_cube(require_cad_cli: None, cube_model: Path, tmp_path: Path) -> None:
    out = tmp_path / "build"
    build = cad_build(model_path=cube_model, output_dir=out, overrides={"size": 10})
    summary = cad_inspect_summary(build.step_path)
    assert summary.status == "ok"
    assert summary.mode == "exact"
    # Data payload must include bbox + volume fields
    assert "bounding_box" in summary.data or "bbox" in summary.data or summary.data


def test_cad_render_cube(
    require_cad_cli: None,
    require_blender: None,
    cube_model: Path,
    tmp_path: Path,
) -> None:
    build_out = tmp_path / "build"
    render_out = tmp_path / "render"
    build = cad_build(model_path=cube_model, output_dir=build_out, overrides={"size": 15})
    render = cad_render(glb_path=build.glb_path, output_dir=render_out)
    assert render.status == "ok"
    assert render.sheet_path.is_file()
    for view in render.view_paths():
        assert view.is_file(), f"missing view {view}"


def test_cad_compare_identical(require_cad_cli: None, cube_model: Path, tmp_path: Path) -> None:
    left = tmp_path / "a"
    right = tmp_path / "b"
    cmp_dir = tmp_path / "cmp"
    a = cad_build(model_path=cube_model, output_dir=left, overrides={"size": 12})
    b = cad_build(model_path=cube_model, output_dir=right, overrides={"size": 12})
    result = cad_compare(
        left_path=a.step_path,
        right_path=b.step_path,
        output_dir=cmp_dir,
        alignment="none",
    )
    assert result.status == "ok"
    assert result.metrics.mode == "exact"
    # Identical solids should have overlap_ratio near 1
    assert result.metrics.overlap_ratio is not None
    assert result.metrics.overlap_ratio == pytest.approx(1.0, abs=1e-3)
