"""`formloop snapshot` command."""

from __future__ import annotations

import json
from collections.abc import Callable

import typer

from ...config.profiles import HarnessConfig


def register(app: typer.Typer, resolve_config: Callable[[], HarnessConfig]) -> None:
    @app.command("snapshot")
    def snapshot_cmd(run_name: str) -> None:
        """Print the snapshot.json for a run."""

        config = resolve_config()
        path = config.runs_dir / run_name / "snapshot.json"
        if not path.is_file():
            typer.echo(f"no snapshot at {path}", err=True)
            raise typer.Exit(code=1)
        typer.echo(json.dumps(json.loads(path.read_text()), indent=2))
