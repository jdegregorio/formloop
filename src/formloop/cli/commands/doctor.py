"""`formloop doctor` command."""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

import typer

from ...config.env import load_env_local, repo_root
from ...runtime.cad_cli import locate_blender, locate_cad


def register(app: typer.Typer) -> None:
    @app.command("doctor")
    def doctor_cmd() -> None:
        """Verify the environment is ready to run the harness (FLH-V-007)."""

        load_env_local()
        problems: list[str] = []

        py = sys.version_info
        if py < (3, 11):
            problems.append(f"Python 3.11+ required; detected {py.major}.{py.minor}.{py.micro}")
        typer.echo(f"python:   {py.major}.{py.minor}.{py.micro}")

        try:
            cad = locate_cad()
            typer.echo(f"cad:      {cad}")
            cad_path = Path(cad).resolve()
            prefix_path = Path(sys.prefix).resolve()
            if not cad_path.is_relative_to(prefix_path):
                problems.append(
                    f"A stray cad shim shadows the venv-local one. "
                    f"Found at: {cad}. Expected inside: {sys.prefix}."
                )
        except Exception:
            cad = None
            typer.echo("cad:      NOT FOUND")
            problems.append("`cad` CLI not found on PATH — run `uv sync` to install cad-cli")

        try:
            blender = locate_blender()
            typer.echo(f"blender:  {blender}")
        except Exception as exc:
            typer.echo(f"blender:  NOT FOUND ({exc})")
            problems.append(str(exc))

        if not os.environ.get("OPENAI_API_KEY"):
            problems.append("OPENAI_API_KEY not set (check .env.local)")
            typer.echo("openai:   NO KEY")
        else:
            typer.echo("openai:   OPENAI_API_KEY present")

        missing_libs = []
        for lib in ("build123d", "bd_warehouse", "py_gearworks"):
            try:
                importlib.import_module(lib)
            except ImportError:
                missing_libs.append(lib)

        if not missing_libs:
            typer.echo("designer libs (formloop venv): ok — bd_warehouse, py_gearworks")
        else:
            typer.echo(f"designer libs (formloop venv): FAILED — missing {', '.join(missing_libs)}")
            problems.append(f"Missing designer libraries in venv: {', '.join(missing_libs)}. Run `uv sync`.")

        if cad is not None:
            try:
                from ...runtime.cad_cli import cad_build

                cube_model = repo_root().parent / "cad-cli" / "examples" / "models" / "cube.py"
                if cube_model.is_file():
                    out = repo_root() / "var" / ".doctor" / "build"
                    if out.exists():
                        shutil.rmtree(out)
                    build = cad_build(model_path=cube_model, output_dir=out, overrides={"size": 5})
                    typer.echo(
                        f"cad build: ok  volume={build.volume:.1f}mm³ "
                        f"bbox={build.bounding_box.size} "
                        f"(--python {sys.executable})"
                    )
                else:
                    typer.echo(f"cad build: skipped (no cube example at {cube_model})")
            except Exception as exc:  # noqa: BLE001 -- diagnostic output
                problems.append(f"cad build smoke failed: {exc}")
                typer.echo(f"cad build: FAILED — {exc}")

        if problems:
            typer.echo("")
            for p in problems:
                typer.echo(f"✗ {p}", err=True)
            raise typer.Exit(code=1)
        typer.echo("")
        typer.echo("all checks passed.")
