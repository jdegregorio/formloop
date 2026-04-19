"""cad-cli runtime boundary for deterministic CAD operations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import ArtifactEntry, ArtifactManifest
from ..paths import sibling_cad_cli_root


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 64), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(slots=True)
class CadBundle:
    manifest: ArtifactManifest
    build_result: dict[str, Any]
    render_result: dict[str, Any]
    inspect_summary: dict[str, Any]


class CadCliRuntime:
    """Execute cad-cli commands and normalize their outputs."""

    # Req: FLH-D-001, FLH-D-004, FLH-D-020, FLH-V-007

    def __init__(self, *, cad_repo_root: Path | None = None, timeout_seconds: int = 300) -> None:
        self.cad_repo_root = cad_repo_root or sibling_cad_cli_root()
        self.timeout_seconds = timeout_seconds

    def _resolve_command_prefix(self) -> list[str]:
        explicit = os.environ.get("FORMLOOP_CAD_COMMAND")
        if explicit:
            return explicit.split(" ")

        sibling_root = self.cad_repo_root
        if (sibling_root / "pyproject.toml").exists():
            return ["uv", "run", "--directory", str(sibling_root), "python", "-m", "cad_cli"]

        installed = shutil.which("cad")
        if installed:
            return [installed]

        raise RuntimeError(
            "Unable to locate cad-cli. Set FORMLOOP_CAD_COMMAND or provide a sibling cad-cli repo."
        )

    def _parse_json_stdout(self, stdout: str) -> dict[str, Any]:
        stdout = stdout.strip()
        for index, char in enumerate(stdout):
            if char not in "{[":
                continue
            candidate = stdout[index:]
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
        raise RuntimeError(f"Could not parse JSON from cad-cli stdout: {stdout}")

    def run_json(self, *args: str, timeout_seconds: int | None = None) -> dict[str, Any]:
        command = [*self._resolve_command_prefix(), *args]
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds or self.timeout_seconds,
        )
        if process.returncode != 0:
            raise RuntimeError(
                f"cad-cli command failed ({process.returncode}): {' '.join(command)}\n"
                f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
            )
        return self._parse_json_stdout(process.stdout)

    def doctor_smoke(self) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="formloop-cad-doctor-") as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            example_model = self.cad_repo_root / "examples" / "models" / "cube.py"
            build = self.run_json(
                "build",
                str(example_model),
                "--output-dir",
                str(tmp_dir / "build"),
                "--format",
                "json",
            )
            inspect_summary = self.run_json(
                "inspect",
                "summary",
                str(tmp_dir / "build" / "model.step"),
                "--format",
                "json",
            )
            return {"build": build, "inspect": inspect_summary}

    def build_render_bundle(self, *, model_path: Path, revision_dir: Path) -> CadBundle:
        build_dir = revision_dir / "_cad_build"
        render_dir = revision_dir / "_cad_render"
        build_result = self.run_json(
            "build",
            str(model_path),
            "--output-dir",
            str(build_dir),
            "--format",
            "json",
        )
        render_result = self.run_json(
            "render",
            str(build_dir / "model.glb"),
            "--output-dir",
            str(render_dir),
            "--format",
            "json",
        )
        inspect_summary = self.run_json(
            "inspect",
            "summary",
            str(build_dir / "model.step"),
            "--format",
            "json",
        )

        step_target = revision_dir / "step.step"
        glb_target = revision_dir / "model.glb"
        sheet_target = revision_dir / "render-sheet.png"
        views_dir = revision_dir / "views"
        views_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(build_dir / "model.step", step_target)
        shutil.copy2(build_dir / "model.glb", glb_target)
        shutil.copy2(render_dir / "sheet.png", sheet_target)

        entries: dict[str, ArtifactEntry] = {}
        for _source_name, role, fmt, target in [
            ("model.step", "step", "step", step_target),
            ("model.glb", "glb", "glb", glb_target),
            ("sheet.png", "render_sheet", "png", sheet_target),
        ]:
            path = target
            entries[role] = ArtifactEntry(
                role=role,
                path=str(path),
                format=fmt,
                required=True,
                sha256=_sha256(path),
                size_bytes=path.stat().st_size,
            )

        for view_name in ("front", "back", "left", "right", "top", "bottom", "iso"):
            source = render_dir / f"{view_name}.png"
            target = views_dir / f"{view_name}.png"
            shutil.copy2(source, target)
            entries[f"view_{view_name}"] = ArtifactEntry(
                role=f"view_{view_name}",
                path=str(target),
                format="png",
                required=True,
                sha256=_sha256(target),
                size_bytes=target.stat().st_size,
            )

        manifest = ArtifactManifest(entries=entries)
        return CadBundle(
            manifest=manifest,
            build_result=build_result,
            render_result=render_result,
            inspect_summary=inspect_summary,
        )

    def compare(
        self,
        *,
        left: Path,
        right: Path,
        output_dir: Path,
        align: str = "principal",
    ) -> dict[str, Any]:
        return self.run_json(
            "compare",
            str(left),
            str(right),
            "--output-dir",
            str(output_dir),
            "--align",
            align,
            "--format",
            "json",
        )
