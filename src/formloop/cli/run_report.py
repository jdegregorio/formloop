"""Header/footer formatting for ``formloop run``.

REQ: FLH-F-027

Keeps the section-rule + boxed-block formatting for the CLI separate from
the live event renderer so the renderer stays focused on streaming events.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from typing import IO

from ._ansi import BOLD, DIM, GREEN, RED, RESET, supports_ansi, terminal_width


def _color(text: str, ansi: str, *, enabled: bool) -> str:
    return f"{ansi}{text}{RESET}" if enabled else text


def _rule(width: int, *, enabled: bool) -> str:
    return _color("─" * width, DIM, enabled=enabled)


def _wrap_indented(text: str, width: int, indent: str = "  ") -> list[str]:
    if not text:
        return []
    out: list[str] = []
    for chunk in text.splitlines() or [text]:
        chunk = chunk.rstrip()
        if not chunk:
            out.append("")
            continue
        out.extend(
            textwrap.wrap(
                chunk,
                width=width,
                initial_indent=indent,
                subsequent_indent=indent,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [indent + chunk]
        )
    return out


def print_run_header(
    *,
    prompt: str,
    profile_name: str,
    model: str,
    reference_image: str | None = None,
    color: bool = True,
    stream: IO[str] | None = None,
) -> None:
    """Print the boxed run header before orchestration starts."""

    out = stream if stream is not None else sys.stdout
    enabled = color and supports_ansi(out)
    width = terminal_width(min_width=60, max_width=120)
    rule = _rule(width, enabled=enabled)
    title = _color("formloop run", BOLD, enabled=enabled)
    meta = _color(f"profile={profile_name}  model={model}", DIM, enabled=enabled)

    out.write(rule + "\n")
    out.write(f" {title}   {meta}\n")
    out.write(rule + "\n")
    out.write(_color("  Request:", BOLD, enabled=enabled) + "\n")
    for line in _wrap_indented(prompt, width=width - 4, indent="    "):
        out.write(line + "\n")
    if reference_image:
        out.write(
            _color(
                f"  Reference image: {Path(reference_image).name}",
                DIM,
                enabled=enabled,
            )
            + "\n"
        )
    out.write("\n")
    out.flush()


def print_run_footer(
    *,
    run_name: str,
    status: str,
    delivered_revision: str | None,
    artifacts_dir: Path | None,
    final_answer: str | None,
    color: bool = True,
    stream: IO[str] | None = None,
) -> None:
    """Print the boxed run footer after orchestration completes."""

    out = stream if stream is not None else sys.stdout
    enabled = color and supports_ansi(out)
    width = terminal_width(min_width=60, max_width=120)
    rule = _rule(width, enabled=enabled)

    out.write("\n")
    out.write(rule + "\n")
    badge_color = GREEN if status == "succeeded" else RED
    badge = _color(
        f"{'✓' if status == 'succeeded' else '✗'} {status}",
        f"{BOLD}{badge_color}",
        enabled=enabled,
    )
    head = _color(f"Run {run_name}", BOLD, enabled=enabled)
    out.write(f" {badge}   {head}\n")
    out.write(rule + "\n")

    if delivered_revision:
        out.write(
            _color("  Delivered revision: ", BOLD, enabled=enabled) + delivered_revision + "\n"
        )
    if artifacts_dir is not None:
        out.write(
            _color("  Artifacts:          ", BOLD, enabled=enabled) + str(artifacts_dir) + "\n"
        )

    if final_answer:
        out.write("\n")
        out.write(_color("  Summary", BOLD, enabled=enabled) + "\n")
        for line in _wrap_indented(final_answer, width=width - 4, indent="    "):
            out.write(line + "\n")
    out.write("\n")
    out.flush()


__all__ = ["print_run_footer", "print_run_header"]
