"""Live event renderer for ``formloop run``.

REQ: FLH-F-024, FLH-F-026, FLH-F-027

The orchestrator streams every ``ProgressEvent`` through ``event_hook``. This
module turns those events into a TTY-friendly live status feed that mirrors
the UI's reasoning-trace pattern: the latest LLM-written narration sits
prominently between the user prompt and the (eventual) final answer, with
older narrations / structured milestones rendered dimmer above.

Three modes:

* ``rich`` (default for TTY): narrations are rewritten in place using ANSI
  cursor controls so the latest one always occupies the same screen line;
  older narrations scroll above as faint history. Structured milestone
  events get a single dimmed line.
* ``plain`` (auto when stdout isn't a TTY, ``NO_COLOR`` is set, or the user
  passed ``--no-color``): one line per event, no ANSI, no in-place rewrite.
* ``verbose``: like plain, but also prints the structured ``data`` payload —
  useful for debugging.

The ``quiet`` flag suppresses narrations and milestone dimmed lines entirely;
only the final summary block printed by the CLI itself remains.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from typing import IO

from ..schemas import ProgressEvent, ProgressEventKind


class RendererMode(str, Enum):
    rich = "rich"
    plain = "plain"
    verbose = "verbose"


# Structured events that are interesting enough to surface (dimmed) even
# in default mode. Everything else is suppressed unless verbose.
_DEFAULT_VISIBLE_KINDS: frozenset[ProgressEventKind] = frozenset(
    {
        ProgressEventKind.spec_normalized,
        ProgressEventKind.research_started,
        ProgressEventKind.research_completed,
        ProgressEventKind.revision_started,
        ProgressEventKind.revision_built,
        ProgressEventKind.revision_persisted,
        ProgressEventKind.review_started,
        ProgressEventKind.review_completed,
        ProgressEventKind.delivered,
        ProgressEventKind.run_failed,
    }
)

# ANSI helpers — stdlib only, kept tiny on purpose (FLH-NF-008).
_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_BOLD = "\x1b[1m"
_RED = "\x1b[31m"
_BLUE = "\x1b[34m"
_CLEAR_LINE = "\x1b[2K"
_CURSOR_UP = "\x1b[1A"
_CURSOR_TO_COL_0 = "\r"


def _supports_ansi(stream: IO[str]) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty"):
        return False
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def _terminal_width(default: int = 100) -> int:
    try:
        return max(40, shutil.get_terminal_size((default, 24)).columns)
    except Exception:
        return default


def _truncate(text: str, width: int) -> str:
    if width <= 1 or len(text) <= width:
        return text
    return text[: max(1, width - 1)] + "…"


@dataclass
class RendererOptions:
    mode: RendererMode = RendererMode.rich
    quiet: bool = False
    color: bool = True


class EventRenderer:
    """Stateful per-run renderer. One instance per ``formloop run`` invocation."""

    def __init__(
        self,
        *,
        stream: IO[str] | None = None,
        options: RendererOptions | None = None,
    ) -> None:
        self.stream = stream if stream is not None else sys.stdout
        self.options = options or RendererOptions()
        # Decide effective mode.
        if not _supports_ansi(self.stream) or not self.options.color:
            if self.options.mode is RendererMode.rich:
                self.options.mode = RendererMode.plain
        self._latest_narration_on_screen = False  # rich mode bookkeeping
        self._last_narration_phase: str | None = None

    # ---- public --------------------------------------------------------

    def __call__(self, event: ProgressEvent) -> None:
        """Hook signature for ``RunDriver(event_hook=...)``."""

        try:
            self._render(event)
        except Exception:
            # Never let a renderer failure abort the run.
            pass

    def finalize(self) -> None:
        """Call once when the run finishes so we leave a clean cursor."""

        if self._latest_narration_on_screen:
            # Move past the in-place narration line so the final summary
            # block prints below cleanly.
            self.stream.write("\n")
            self._latest_narration_on_screen = False
            self.stream.flush()

    # ---- internals -----------------------------------------------------

    def _render(self, event: ProgressEvent) -> None:
        if self.options.quiet:
            # Quiet mode: only failures escape.
            if event.kind is ProgressEventKind.run_failed:
                self._write_failure(event)
            return

        if event.kind is ProgressEventKind.narration:
            self._render_narration(event)
            return

        if event.kind is ProgressEventKind.run_failed:
            self._write_failure(event)
            return

        if self.options.mode is RendererMode.verbose:
            self._render_milestone_verbose(event)
            return

        if event.kind in _DEFAULT_VISIBLE_KINDS:
            self._render_milestone_dimmed(event)

    def _render_narration(self, event: ProgressEvent) -> None:
        text = (event.message or "").strip()
        if not text:
            return
        width = _terminal_width()
        prefix = "› "
        line = _truncate(prefix + text, width)
        if self.options.mode is RendererMode.rich:
            # In rich mode we rewrite the previous narration line in place
            # so the latest narration always occupies the same row, like
            # the UI's reasoning-trace component. Previous narrations are
            # promoted to dimmed history lines.
            if self._latest_narration_on_screen:
                # Move up over the live line, clear it, then write the
                # previous text as a dimmed history line in its place
                # before emitting the new live line below.
                self.stream.write(_CURSOR_UP + _CURSOR_TO_COL_0 + _CLEAR_LINE)
                # Promote the just-replaced narration to dimmed history.
                # We can't recover the old text from the screen, so we
                # just emit a faint marker — the full trace lives in the
                # events file anyway.
                self.stream.write(_DIM + "  ·\n" + _RESET)
            self.stream.write(_BOLD + line + _RESET + "\n")
            self._latest_narration_on_screen = True
        else:
            # Plain / verbose: lead with the narration marker so the line
            # is visually distinct from milestone lines, with the phase
            # tag trailing in brackets for context.
            phase_suffix = f"  [{event.phase}]" if event.phase else ""
            full = line + phase_suffix
            full = _truncate(full, width)
            self.stream.write(full + "\n")
            if event.narration_error:
                self.stream.write(
                    f"  (narrator fallback: {event.narration_error})\n"
                )
        self._last_narration_phase = event.phase
        self.stream.flush()

    def _render_milestone_dimmed(self, event: ProgressEvent) -> None:
        # In rich mode, milestones print *above* the in-place narration,
        # so we have to scroll the narration down by one line to keep the
        # ordering right. Easiest path: clear the live line, write the
        # milestone, then re-emit the live narration placeholder.
        text = self._milestone_text(event)
        width = _terminal_width()
        line = _truncate("  · " + text, width)
        if (
            self.options.mode is RendererMode.rich
            and self._latest_narration_on_screen
        ):
            self.stream.write(_CURSOR_UP + _CURSOR_TO_COL_0 + _CLEAR_LINE)
            self.stream.write(_DIM + line + _RESET + "\n")
            # Live narration is no longer on screen — finalize() / next
            # narration will redraw it. We mark it absent so the next
            # narration prints fresh.
            self._latest_narration_on_screen = False
        else:
            if self.options.mode is RendererMode.rich:
                self.stream.write(_DIM + line + _RESET + "\n")
            else:
                self.stream.write(line + "\n")
        self.stream.flush()

    def _render_milestone_verbose(self, event: ProgressEvent) -> None:
        line = (
            f"[{event.index:03d}] {event.kind.value}: {event.message}"
        )
        self.stream.write(line + "\n")
        if event.data:
            import json

            self.stream.write("  data: " + json.dumps(event.data, default=str) + "\n")
        self.stream.flush()

    def _milestone_text(self, event: ProgressEvent) -> str:
        # Prefer the structured message; fall back to the kind name.
        return event.message or event.kind.value.replace("_", " ")

    def _write_failure(self, event: ProgressEvent) -> None:
        if (
            self.options.mode is RendererMode.rich
            and self._latest_narration_on_screen
        ):
            self.stream.write(_CURSOR_UP + _CURSOR_TO_COL_0 + _CLEAR_LINE)
            self._latest_narration_on_screen = False
        text = f"✗ {event.message or 'run failed'}"
        if self.options.color and self.options.mode is RendererMode.rich:
            self.stream.write(_BOLD + _RED + text + _RESET + "\n")
        else:
            self.stream.write(text + "\n")
        self.stream.flush()


def make_renderer(
    *,
    quiet: bool = False,
    verbose: bool = False,
    color: bool = True,
    stream: IO[str] | None = None,
) -> EventRenderer:
    """Pick the right mode given user flags + TTY detection."""

    if quiet and verbose:
        # quiet wins; verbose is meaningless when nothing is shown.
        verbose = False
    if verbose:
        mode = RendererMode.verbose
    else:
        mode = RendererMode.rich  # downgraded inside EventRenderer if no TTY
    return EventRenderer(
        stream=stream,
        options=RendererOptions(mode=mode, quiet=quiet, color=color),
    )


__all__ = [
    "EventRenderer",
    "RendererMode",
    "RendererOptions",
    "make_renderer",
]
