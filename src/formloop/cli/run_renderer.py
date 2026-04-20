"""Live event renderer for ``formloop run``.

REQ: FLH-F-024, FLH-F-026, FLH-F-027

The orchestrator streams every ``ProgressEvent`` through ``event_hook``. This
module turns those events into a TTY-friendly live status feed.

Design notes:

* The terminal is append-only — unlike the UI, there's no "expand history"
  affordance, so every narration must remain visible. Long narrations are
  word-wrapped with a hanging indent rather than truncated. The screen never
  rewrites prior lines.
* Structured milestone events are dimmed and prefixed with ``·`` so they
  read as supporting context next to the bolder narration lines.
* ``--quiet`` suppresses everything except failures (which always escape).
* ``--verbose`` prints each event with its raw ``data`` payload — useful for
  debugging the orchestrator.
* When stdout isn't a TTY (or ``NO_COLOR`` is set, or ``--no-color`` was
  passed) we strip ANSI but keep the same line layout.
"""

from __future__ import annotations

import os
import shutil
import sys
import textwrap
from dataclasses import dataclass
from enum import Enum
from typing import IO

from ..schemas import ProgressEvent, ProgressEventKind


class RendererMode(str, Enum):
    rich = "rich"  # color + pretty layout (TTY default)
    plain = "plain"  # same layout, no ANSI
    verbose = "verbose"  # plain layout + raw data payloads


# Structured events that are interesting enough to surface (dimmed) even
# in default mode. Everything else is suppressed unless verbose.
_DEFAULT_VISIBLE_KINDS: frozenset[ProgressEventKind] = frozenset(
    {
        ProgressEventKind.spec_normalized,
        ProgressEventKind.assumption_recorded,
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
_GREEN = "\x1b[32m"
_YELLOW = "\x1b[33m"
_CYAN = "\x1b[36m"

NARRATION_MARKER = "›"
MILESTONE_MARKER = "·"
ASSUMPTION_MARKER = "↳"
FAILURE_MARKER = "✗"


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


def _wrap(text: str, *, width: int, initial_indent: str, subsequent_indent: str) -> str:
    """Word-wrap ``text`` to ``width`` with the given indents.

    Falls back to a single line when the input is short. Preserves explicit
    paragraph breaks (``\\n``) by wrapping each chunk independently.
    """

    if not text:
        return initial_indent.rstrip()
    chunks = text.splitlines() or [text]
    out_lines: list[str] = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk:
            out_lines.append("")
            continue
        wrapper = textwrap.TextWrapper(
            width=max(20, width),
            initial_indent=initial_indent if i == 0 else subsequent_indent,
            subsequent_indent=subsequent_indent,
            break_long_words=False,
            break_on_hyphens=False,
        )
        out_lines.append(wrapper.fill(chunk))
    return "\n".join(out_lines)


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
        # Decide effective mode — rich requires both a TTY and color enabled.
        if not _supports_ansi(self.stream) or not self.options.color:
            if self.options.mode is RendererMode.rich:
                self.options.mode = RendererMode.plain
        self._last_phase: str | None = None
        # Track whether anything has been printed yet, so we can pad blocks
        # nicely without leading blank lines.
        self._printed_any = False

    # ---- public --------------------------------------------------------

    def __call__(self, event: ProgressEvent) -> None:
        """Hook signature for ``RunDriver(event_hook=...)``."""

        try:
            self._render(event)
        except Exception:
            # Never let a renderer failure abort the run.
            pass

    def finalize(self) -> None:
        """Call once when the run finishes. No cursor cleanup needed in
        append-only mode, but kept on the public API for callers."""

        return None

    # ---- internals -----------------------------------------------------

    def _color(self, ansi: str, text: str) -> str:
        if self.options.color and self.options.mode is RendererMode.rich:
            return f"{ansi}{text}{_RESET}"
        return text

    def _print(self, line: str) -> None:
        self.stream.write(line.rstrip("\n") + "\n")
        self.stream.flush()
        self._printed_any = True

    def _render(self, event: ProgressEvent) -> None:
        if self.options.quiet:
            if event.kind is ProgressEventKind.run_failed:
                self._render_failure(event)
            return

        if event.kind is ProgressEventKind.narration:
            self._render_narration(event)
            return

        if event.kind is ProgressEventKind.run_failed:
            self._render_failure(event)
            return

        if self.options.mode is RendererMode.verbose:
            self._render_milestone_verbose(event)
            return

        if event.kind in _DEFAULT_VISIBLE_KINDS:
            self._render_milestone(event)

    # ---- narration -----------------------------------------------------

    def _render_narration(self, event: ProgressEvent) -> None:
        text = (event.message or "").strip()
        if not text:
            return
        width = _terminal_width()
        phase = event.phase or "…"
        # First-line prefix shows phase + marker so readers can scan the
        # left margin to follow the run's progression. Continuation lines
        # indent under the text so the wrap reads as one paragraph.
        phase_tag = f"[{phase}]"
        initial = f"  {NARRATION_MARKER} {self._color(_DIM, phase_tag)} "
        # Visible width of the colored phase tag is its character length —
        # ANSI escapes are zero-width, so we measure on the raw tag.
        visible_prefix_len = len(f"  {NARRATION_MARKER} {phase_tag} ")
        subsequent = " " * visible_prefix_len
        body = _wrap(text, width=width, initial_indent="", subsequent_indent="")
        # Wrap manually so the colored prefix isn't counted into the width.
        wrapped = textwrap.fill(
            body,
            width=max(20, width),
            initial_indent="",
            subsequent_indent=subsequent,
            break_long_words=False,
            break_on_hyphens=False,
        )
        # Insert prefix before the first line.
        first, _, rest = wrapped.partition("\n")
        line = self._color(_BOLD, initial + first)
        if rest:
            line = line + "\n" + rest
        self._print(line)
        if event.narration_error:
            self._print(
                self._color(_DIM, f"    (narrator fallback: {event.narration_error})")
            )
        self._last_phase = event.phase

    # ---- milestones ----------------------------------------------------

    def _render_milestone(self, event: ProgressEvent) -> None:
        """Render a structured milestone event with kind-specific polish."""

        kind = event.kind
        width = _terminal_width()

        if kind is ProgressEventKind.spec_normalized:
            self._render_spec_normalized(event, width=width)
            return
        if kind is ProgressEventKind.assumption_recorded:
            self._render_assumption(event, width=width)
            return
        if kind is ProgressEventKind.research_started:
            topics = event.data.get("topics") or []
            count = len(topics) if isinstance(topics, list) else event.data.get(
                "count", 0
            )
            text = f"researching {count} topic{'s' if count != 1 else ''}"
            self._render_milestone_line(text, width=width)
            if isinstance(topics, list) and topics:
                for t in topics[:6]:
                    self._render_indent_line(f"- {t}", width=width)
            return
        if kind is ProgressEventKind.research_completed:
            count = event.data.get("count", 0)
            self._render_milestone_line(
                f"research complete ({count} finding{'s' if count != 1 else ''})",
                width=width,
            )
            return
        if kind is ProgressEventKind.revision_started:
            attempt = event.data.get("attempt")
            label = (
                f"revision attempt {attempt}" if attempt else (event.message or "revision")
            )
            self._render_milestone_line(label, width=width)
            return
        if kind is ProgressEventKind.revision_built:
            data = event.data
            parts = []
            if "build_ok" in data:
                parts.append(f"build={'ok' if data['build_ok'] else 'FAIL'}")
            if "render_ok" in data:
                parts.append(f"render={'ok' if data['render_ok'] else 'FAIL'}")
            if "inspect_ok" in data:
                parts.append(f"inspect={'ok' if data['inspect_ok'] else 'FAIL'}")
            text = "designer returned " + " ".join(parts) if parts else (
                event.message or "designer returned"
            )
            self._render_milestone_line(text, width=width)
            dims = data.get("dimensions")
            if isinstance(dims, dict) and dims:
                summary = ", ".join(
                    f"{k}={v}" for k, v in list(dims.items())[:6]
                )
                self._render_indent_line(summary, width=width)
            return
        if kind is ProgressEventKind.revision_persisted:
            rev = event.data.get("revision") or event.message
            self._render_milestone_line(f"persisted {rev}", width=width)
            return
        if kind is ProgressEventKind.review_started:
            rev = event.data.get("revision")
            text = f"reviewing {rev}" if rev else (event.message or "reviewing")
            self._render_milestone_line(text, width=width)
            return
        if kind is ProgressEventKind.review_completed:
            decision = event.data.get("decision") or "?"
            confidence = event.data.get("confidence")
            text = f"review decision: {decision}"
            if isinstance(confidence, (int, float)):
                text += f" (confidence {confidence:.2f})"
            decorated = (
                self._color(_GREEN, text)
                if decision == "pass"
                else self._color(_YELLOW, text)
            )
            # Render manually so we keep the milestone marker but use a
            # decision-colored body instead of the default dim treatment.
            self._print(f"  {self._color(_DIM, MILESTONE_MARKER)} {decorated}")
            return
        if kind is ProgressEventKind.delivered:
            rev = event.data.get("revision")
            status = event.data.get("status")
            text = "delivered"
            if rev:
                text += f" {rev}"
            if status:
                text += f" ({status})"
            decorated = (
                self._color(_GREEN, text)
                if status == "succeeded"
                else self._color(_YELLOW, text)
            )
            self._print(f"  {self._color(_DIM, MILESTONE_MARKER)} {decorated}")
            return

        # Fallback: just print the message dimly.
        self._render_milestone_line(event.message or kind.value.replace("_", " "), width=width)

    def _render_milestone_line(self, text: str, *, width: int) -> None:
        prefix = f"  {MILESTONE_MARKER} "
        body = _wrap(
            text,
            width=width,
            initial_indent="",
            subsequent_indent=" " * len(prefix),
        )
        first, _, rest = body.partition("\n")
        line = self._color(_DIM, prefix + first)
        if rest:
            line += "\n" + self._color(_DIM, rest)
        self._print(line)

    def _render_indent_line(self, text: str, *, width: int) -> None:
        prefix = "      "  # under the milestone marker
        wrapped = _wrap(
            text, width=width, initial_indent=prefix, subsequent_indent=prefix + "  "
        )
        self._print(self._color(_DIM, wrapped))

    def _render_spec_normalized(self, event: ProgressEvent, *, width: int) -> None:
        data = event.data
        brief = data.get("design_brief") or ""
        kind_label = data.get("spec_kind") or ""
        assumption_count = data.get("assumption_count")
        research_count = data.get("research_topic_count")
        head = "spec normalized"
        if kind_label:
            head += f" — {kind_label}"
        meta_bits = []
        if isinstance(assumption_count, int) and assumption_count:
            meta_bits.append(
                f"{assumption_count} assumption{'s' if assumption_count != 1 else ''}"
            )
        if isinstance(research_count, int) and research_count:
            meta_bits.append(
                f"{research_count} research topic{'s' if research_count != 1 else ''}"
            )
        if meta_bits:
            head += " (" + ", ".join(meta_bits) + ")"
        self._render_milestone_line(head, width=width)
        if brief:
            self._render_indent_line(brief, width=width)

    def _render_assumption(self, event: ProgressEvent, *, width: int) -> None:
        topic = event.data.get("topic") or ""
        assumption = event.data.get("assumption") or event.message or ""
        text = f"{ASSUMPTION_MARKER} {topic}: {assumption}" if topic else assumption
        prefix = "      "
        wrapped = _wrap(
            text, width=width, initial_indent=prefix, subsequent_indent=prefix + "  "
        )
        self._print(self._color(_DIM, wrapped))

    # ---- failure / verbose ---------------------------------------------

    def _render_failure(self, event: ProgressEvent) -> None:
        text = f"{FAILURE_MARKER} {event.message or 'run failed'}"
        if self.options.color and self.options.mode is RendererMode.rich:
            self._print(_BOLD + _RED + text + _RESET)
        else:
            self._print(text)

    def _render_milestone_verbose(self, event: ProgressEvent) -> None:
        line = f"[{event.index:03d}] {event.kind.value}: {event.message}"
        self._print(line)
        if event.data:
            import json

            self._print("  data: " + json.dumps(event.data, default=str))


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
    "NARRATION_MARKER",
    "MILESTONE_MARKER",
]
