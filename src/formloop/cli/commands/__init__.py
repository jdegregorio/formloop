"""Typer-based operator CLI.

REQ: FLH-F-012, FLH-F-013, FLH-F-027, FLH-D-015, FLH-D-016, FLH-V-007
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import typer

from ...config.env import load_env_local
from ...config.profiles import HarnessConfig, load_config
from . import doctor, eval, run, snapshot, ui

app = typer.Typer(
    name="formloop",
    help="Formloop harness operator CLI.",
    no_args_is_help=True,
    add_completion=False,
)


eval_app = typer.Typer(help="Eval batch runner / reporting.")
ui_app = typer.Typer(help="Manage the polling HTTP API daemon.")

app.add_typer(eval_app, name="eval")
app.add_typer(ui_app, name="ui")


def _resolve_config() -> HarnessConfig:
    load_env_local()
    return load_config()


run.register(app, _resolve_config)
eval.register(eval_app, _resolve_config)
ui.register(ui_app, _resolve_config)
doctor.register(app)
snapshot.register(app, _resolve_config)


@app.command("update")
def update_cmd() -> None:
    """Report current formloop version and offer an update command hint."""

    try:
        ver = version("formloop")
    except PackageNotFoundError:
        ver = "unknown (not installed via pip/uv)"
    typer.echo(f"formloop: {ver}")
    typer.echo("To upgrade inside this worktree: `uv sync`")
