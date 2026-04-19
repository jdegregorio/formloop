"""Pre-build ground-truth STEP files for eval cases.

Usage: uv run python scripts/build_ground_truth.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from formloop.runtime.cad_cli import cad_build


DATASET = Path(__file__).resolve().parents[1] / "datasets" / "basic_shapes"


def build_case(seed_name: str, ground_truth_name: str, overrides: dict | None = None) -> None:
    seed = DATASET / "seed_models" / seed_name
    out_dir = DATASET / "_build" / seed.stem
    if out_dir.exists():
        shutil.rmtree(out_dir)
    result = cad_build(model_path=seed, output_dir=out_dir, overrides=overrides or {})
    dst = DATASET / "ground_truth" / ground_truth_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(result.step_path.read_bytes())
    print(f"built {dst} (volume={result.volume:.2f} mm³)")


def main() -> int:
    build_case("cube_20mm.py", "cube_20mm.step", overrides={"size": 20})
    build_case(
        "plate_two_holes.py",
        "plate_two_holes.step",
        overrides={
            "width": 40,
            "depth": 24,
            "height": 8,
            "hole_diameter": 6,
            "hole_centers": [[-10.0, 0.0], [10.0, 0.0]],
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
