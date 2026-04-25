"""`formloop run` command."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from ...config.env import require_openai_key
from ...config.profiles import HarnessConfig
from ...orchestrator import drive_run
from ..run_renderer import make_renderer
from ..run_report import print_run_footer, print_run_header


def register(app: typer.Typer, resolve_config: Callable[[], HarnessConfig]) -> None:
    @app.command("run")
    def run_cmd(
        prompt: Annotated[str, typer.Argument(help="Natural-language design request.")],
        profile: Annotated[
            str | None,
            typer.Option("--profile", help="Profile name from formloop.harness.toml."),
        ] = None,
        model: Annotated[
            str | None,
            typer.Option("--model", help="Override the model (e.g. gpt-5.4-nano)."),
        ] = None,
        effort: Annotated[
            str | None,
            typer.Option("--effort", help="Override reasoning effort: low | medium | high."),
        ] = None,
        reference_image: Annotated[
            Path | None,
            typer.Option("--reference-image", help="Optional reference image path."),
        ] = None,
        max_revisions: Annotated[
            int | None,
            typer.Option("--max-revisions", help="Override max revision attempts."),
        ] = None,
        post_mortem: Annotated[
            bool,
            typer.Option(
                "--post-mortem/--no-post-mortem",
                help=(
                    "After the run completes, ask an LLM to draft harness "
                    "optimization issues from this run's logs/events/errors."
                ),
            ),
        ] = False,
        quiet: Annotated[
            bool,
            typer.Option(
                "--quiet",
                "-q",
                help="Suppress live narration; only show the final result.",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Show every event with its data payload (debugging).",
            ),
        ] = False,
        no_color: Annotated[
            bool,
            typer.Option("--no-color", help="Disable ANSI colors / in-place narration rewrite."),
        ] = False,
    ) -> None:
        """Run the harness end-to-end for a single prompt (FLH-F-012, FLH-F-027)."""

        config: HarnessConfig = resolve_config()
        ref = str(reference_image.resolve()) if reference_image else None
        resolved_profile = config.profile(profile)

        renderer = make_renderer(quiet=quiet, verbose=verbose, color=not no_color)

        if not quiet:
            print_run_header(
                prompt=prompt,
                profile_name=resolved_profile.name,
                model=model or resolved_profile.model,
                reference_image=ref,
                color=not no_color,
            )

        try:
            require_openai_key()
        except RuntimeError as exc:
            typer.echo(f"formloop run failed: {exc}", err=True)
            raise typer.Exit(code=2) from exc

        try:
            result = asyncio.run(
                drive_run(
                    prompt,
                    config=config,
                    profile=profile,
                    model=model,
                    effort=effort,
                    reference_image=ref,
                    max_revisions=max_revisions,
                    post_mortem=post_mortem,
                    event_hook=renderer,
                )
            )
        except Exception as exc:  # noqa: BLE001 -- CLI boundary should not traceback.
            typer.echo(f"formloop run failed: {type(exc).__name__}: {exc}", err=True)
            raise typer.Exit(code=2) from exc

        if not quiet:
            print_run_footer(
                run_name=result["run_name"],
                status=result["status"],
                delivered_revision=result.get("delivered_revision"),
                artifacts_dir=(
                    config.runs_dir
                    / result["run_name"]
                    / "revisions"
                    / result["delivered_revision"]
                    if result.get("delivered_revision")
                    else None
                ),
                final_answer=result.get("final_answer"),
                color=not no_color,
            )

        if result["status"] != "succeeded":
            raise typer.Exit(code=2)
