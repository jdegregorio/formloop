from __future__ import annotations

from pathlib import Path
import json
import subprocess

import pytest

from formloop.agents.skills import load_builtin_skill_texts
from formloop.datasets import load_eval_cases


def test_load_builtin_skill_texts_returns_known_skill(repo_root: Path) -> None:
    skills = load_builtin_skill_texts(repo_root / "src" / "formloop" / "builtin_skills")
    assert "build123d_modeling" in skills


def test_load_eval_cases_raises_for_missing_dataset(repo_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_eval_cases(repo_root / "datasets", "missing_dataset")


def test_fake_cad_extracts_dimensions_and_reports_them(repo_root: Path, tmp_path: Path) -> None:
    model_source = tmp_path / "model.py"
    model_source.write_text(
        "\n".join(
            [
                "from build123d import *",
                "length_x = 150",
                "width_y = 75",
                "thickness = 6",
                "hole_spacing = 50",
                "m3_tap_drill_d = 2.5",
                "chamfer_amount = 0.5",
                "# bracket",
            ]
        ),
        encoding="utf-8",
    )
    fake_cad = repo_root / "scripts" / "fake_cad"
    build_dir = tmp_path / "build"
    render_dir = tmp_path / "render"

    build = subprocess.run(
        [str(fake_cad), "build", "--model-source", str(model_source), "--output-dir", str(build_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    build_payload = json.loads(build.stdout)

    render = subprocess.run(
        [str(fake_cad), "render", "--glb-path", build_payload["glb_path"], "--output-dir", str(render_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    render_payload = json.loads(render.stdout)

    inspect = subprocess.run(
        [
            str(fake_cad),
            "inspect",
            "--step-path",
            build_payload["step_path"],
            "--measurements",
            json.dumps(
                [
                    "Plate thickness: 6mm",
                    "Hole center-to-center spacing: 50mm",
                    "0.5mm chamfer on all outer edges",
                    "Overall size: 75mm x 150mm",
                ]
            ),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    inspect_payload = json.loads(inspect.stdout)

    assert Path(render_payload["render_sheet_path"]).exists()
    assert render_payload["metadata_path"]
    assert inspect_payload["measurements"]["Plate thickness: 6mm"] == 6.0
    assert inspect_payload["measurements"]["Hole center-to-center spacing: 50mm"] == 50.0
    assert inspect_payload["measurements"]["0.5mm chamfer on all outer edges"] == 0.5
    assert inspect_payload["measurements"]["Overall size: 75mm x 150mm"] == "length=150.0, width=75.0, thickness=6.0"
