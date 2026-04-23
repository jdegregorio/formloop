"""`formloop doctor` command."""

from __future__ import annotations

import os
import shutil
import sys

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
            problems.append(
                f"Python 3.11+ required; detected {py.major}.{py.minor}.{py.micro}"
            )
        typer.echo(f"python:   {py.major}.{py.minor}.{py.micro}")

        cad = locate_cad()
        typer.echo(f"cad:      {cad}")
        if cad is None:
            problems.append("`cad` CLI not found on PATH — install cad-cli editable")

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

        if cad is not None:
            try:
                from ...runtime.cad_cli import cad_build

                cube_model = (
                    repo_root().parent / "cad-cli" / "examples" / "models" / "cube.py"
                )
                if cube_model.is_file():
                    out = repo_root() / "var" / ".doctor" / "build"
                    if out.exists():
                        shutil.rmtree(out)
                    build = cad_build(
                        model_path=cube_model, output_dir=out, overrides={"size": 5}
                    )
                    typer.echo(
                        f"cad build: ok  volume={build.volume:.1f}mm³ "
                        f"bbox={build.bounding_box.size}"
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
