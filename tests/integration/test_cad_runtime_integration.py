from __future__ import annotations

from pathlib import Path

from formloop.paths import sibling_cad_cli_root
from formloop.runtime.cad import CadCliRuntime


def test_flh_d_001_and_flh_d_020_runtime_builds_and_maps_bundle(tmp_path: Path) -> None:
    runtime = CadCliRuntime()
    source = sibling_cad_cli_root() / "examples" / "models" / "cube.py"
    bundle = runtime.build_render_bundle(model_path=source, revision_dir=tmp_path / "rev-001")
    assert (tmp_path / "rev-001" / "step.step").exists()
    assert (tmp_path / "rev-001" / "model.glb").exists()
    assert (tmp_path / "rev-001" / "render-sheet.png").exists()
    assert "render_sheet" in bundle.manifest.entries
    assert "view_iso" in bundle.manifest.entries
