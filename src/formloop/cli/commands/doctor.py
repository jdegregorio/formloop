"""`formloop doctor` command."""

from __future__ import annotations

import importlib
import os
import shutil
import sys
import textwrap
from pathlib import Path

import typer

from ...config.env import load_env_local, repo_root
from ...runtime.cad_cli import locate_blender, locate_cad


def _check_designer_libraries() -> tuple[list[str], list[str]]:
    """Return (importable, missing) lists for designer-advertised libraries.

    Imports happen against the formloop interpreter (i.e. ``sys.executable``),
    which is the same interpreter ``cad build --python`` uses to evaluate
    model.py. So these results are exactly what the designer will see at build
    time.
    """

    from ...agents.cad_designer import AVAILABLE_BUILD123D_LIBRARIES

    importable: list[str] = []
    missing: list[str] = []
    for name in AVAILABLE_BUILD123D_LIBRARIES:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 -- diagnostic
            missing.append(f"{name} ({type(exc).__name__}: {exc})")
        else:
            importable.append(name)
    return importable, missing


def register(app: typer.Typer) -> None:
    @app.command("doctor")
    def doctor_cmd() -> None:
        """Verify the environment is ready to run the harness (FLH-V-007)."""

        load_env_local()
        problems: list[str] = []

        py = sys.version_info
        if py < (3, 12):
            problems.append(f"Python 3.12+ required; detected {py.major}.{py.minor}.{py.micro}")
        typer.echo(f"python:       {py.major}.{py.minor}.{py.micro} ({sys.executable})")

        cad = locate_cad()
        typer.echo(f"cad:          {cad}")
        if cad is None:
            problems.append("`cad` CLI not found — run `uv sync` to install cad-cli")
        else:
            venv_local = Path(sys.executable).parent / "cad"
            global_cad = shutil.which("cad")
            if (
                venv_local.is_file()
                and global_cad
                and Path(global_cad).resolve() != venv_local.resolve()
            ):
                typer.echo(
                    f"              note: a different `cad` is also on PATH at {global_cad}; "
                    "the venv-local one is preferred."
                )

        try:
            blender = locate_blender()
        except Exception as exc:
            blender = None
            typer.echo(f"blender:      NOT FOUND ({exc})")
            problems.append(str(exc))
        if blender:
            typer.echo(f"blender:      {blender}")
        else:
            typer.echo("blender:      NOT FOUND")
            problems.append(
                "Blender not found — install via "
                "`brew install --cask blender` (macOS) or your platform package."
            )

        if not os.environ.get("OPENAI_API_KEY"):
            problems.append("OPENAI_API_KEY not set (check .env.local)")
            typer.echo("openai:       NO KEY")
        else:
            typer.echo("openai:       OPENAI_API_KEY present")

        importable, missing = _check_designer_libraries()
        if importable:
            typer.echo(f"designer libs (formloop venv): ok — {', '.join(importable)}")
        if missing:
            typer.echo("designer libs (formloop venv): MISSING")
            for entry in missing:
                typer.echo(f"              - {entry}")
            problems.append(
                "designer-advertised libraries are not importable in the formloop venv: "
                + ", ".join(name.split(" ")[0] for name in missing)
            )

        if cad is not None:
            try:
                from ...runtime.cad_cli import cad_build

                cube_model = repo_root() / "examples" / "models" / "cube.py"
                if not cube_model.is_file():
                    cube_model = repo_root().parent / "cad-cli" / "examples" / "models" / "cube.py"
                if cube_model.is_file():
                    out = repo_root() / "var" / ".doctor" / "build"
                    if out.exists():
                        shutil.rmtree(out)
                    build = cad_build(model_path=cube_model, output_dir=out, overrides={"size": 5})
                    typer.echo(
                        f"cad build:    ok  volume={build.volume:.1f}mm³ "
                        f"bbox={build.bounding_box.size}"
                    )
                    typer.echo(
                        "              (model evaluated via "
                        f"--python {sys.executable})"
                    )
                else:
                    typer.echo(f"cad build:    skipped (no cube example at {cube_model})")
            except Exception as exc:  # noqa: BLE001 -- diagnostic output
                problems.append(f"cad build smoke failed: {exc}")
                typer.echo(f"cad build:    FAILED — {exc}")

        if problems:
            typer.echo("")
            for p in problems:
                typer.echo(f"✗ {p}", err=True)
            typer.echo("")
            typer.echo(
                textwrap.dedent(
                    """\
                    Tips:
                      - run `uv sync --extra dev` to (re)install Python deps
                      - install Blender (`brew install --cask blender` on macOS)
                      - copy `.env.example` to `.env.local` and add OPENAI_API_KEY
                    """
                ),
                err=True,
            )
            raise typer.Exit(code=1)
        typer.echo("")
        typer.echo("all checks passed.")
