"""`formloop eval` command group."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from ...config.profiles import HarnessConfig
from ..role_overrides import parse_role_assignments


def register(eval_app: typer.Typer, resolve_config: Callable[[], HarnessConfig]) -> None:
    @eval_app.command("run")
    def eval_run_cmd(
        dataset_path: Annotated[Path, typer.Argument(help="Path to cases.jsonl.")],
        profile: Annotated[str | None, typer.Option("--profile")] = None,
        model: Annotated[
            str | None,
            typer.Option("--model", help="Override the model (e.g. gpt-5.4-nano)."),
        ] = None,
        effort: Annotated[
            str | None,
            typer.Option("--effort", help="Override reasoning effort: low | medium | high."),
        ] = None,
        batch_name: Annotated[str | None, typer.Option("--batch-name")] = None,
        max_revisions: Annotated[int | None, typer.Option("--max-revisions")] = None,
        role_model: Annotated[
            list[str] | None,
            typer.Option("--role-model", help="Per-role model override as ROLE=MODEL. Repeatable."),
        ] = None,
        role_effort: Annotated[
            list[str] | None,
            typer.Option(
                "--role-effort", help="Per-role reasoning override as ROLE=EFFORT. Repeatable."
            ),
        ] = None,
    ) -> None:
        """Run an eval batch (FLH-F-014, FLH-D-018)."""

        from ...evals.runner import run_eval_batch

        config = resolve_config()
        try:
            role_model_overrides = parse_role_assignments(role_model)
            role_reasoning_overrides = parse_role_assignments(role_effort, validate_values=True)
        except ValueError as exc:
            typer.echo(f"formloop eval run failed: {exc}", err=True)
            raise typer.Exit(code=2) from exc
        asyncio.run(
            run_eval_batch(
                dataset_path=dataset_path,
                config=config,
                profile=profile,
                model=model,
                effort=effort,
                batch_name=batch_name,
                max_revisions=max_revisions,
                role_model_overrides=role_model_overrides,
                role_reasoning_overrides=role_reasoning_overrides,
            )
        )

    @eval_app.command("report")
    def eval_report_cmd(
        batch: Annotated[str, typer.Argument(help="Batch name or 'latest'.")] = "latest",
    ) -> None:
        """Render aggregated eval report for a batch."""

        from ...evals.report import render_report

        config = resolve_config()
        path = render_report(config, batch)
        typer.echo(f"report: {path}")
