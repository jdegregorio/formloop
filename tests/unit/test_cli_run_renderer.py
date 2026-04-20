"""CLI live renderer behavior.

REQ: FLH-F-024, FLH-F-026, FLH-F-027
"""

from __future__ import annotations

import io

import pytest

from formloop.cli.run_renderer import (
    EventRenderer,
    RendererMode,
    RendererOptions,
    make_renderer,
)
from formloop.schemas import ProgressEvent, ProgressEventKind


def _ev(
    index: int,
    kind: ProgressEventKind,
    message: str = "",
    *,
    phase: str | None = None,
    narration_error: str | None = None,
    data: dict | None = None,
) -> ProgressEvent:
    return ProgressEvent(
        index=index,
        kind=kind,
        message=message,
        phase=phase,
        narration_error=narration_error,
        data=data or {},
    )


# A non-TTY io.StringIO triggers the auto-downgrade to plain mode, which is
# exactly what we want for deterministic assertions.


def _renderer(
    *, quiet: bool = False, verbose: bool = False, color: bool = False
) -> tuple[EventRenderer, io.StringIO]:
    buf = io.StringIO()
    r = make_renderer(quiet=quiet, verbose=verbose, color=color, stream=buf)
    return r, buf


def test_narration_renders_with_marker_in_plain_mode() -> None:
    r, buf = _renderer()
    r(_ev(3, ProgressEventKind.narration, "we normalized the spec", phase="plan"))
    out = buf.getvalue()
    assert "we normalized the spec" in out
    assert "›" in out
    assert "[plan]" in out


def test_milestones_render_distinctly_from_narrations() -> None:
    r, buf = _renderer()
    r(_ev(1, ProgressEventKind.spec_normalized, "spec normalized"))
    r(_ev(2, ProgressEventKind.narration, "we normalized the spec", phase="plan"))
    lines = [line for line in buf.getvalue().splitlines() if line.strip()]
    # Milestone uses the · marker; narration uses the › marker. Both must
    # appear, and they must come from different lines (so the two event
    # classes are visually distinct).
    milestone_lines = [line for line in lines if "·" in line and "›" not in line]
    narration_lines = [line for line in lines if "›" in line]
    assert milestone_lines, lines
    assert narration_lines, lines


def test_quiet_suppresses_narration_and_milestones() -> None:
    r, buf = _renderer(quiet=True)
    r(_ev(1, ProgressEventKind.spec_normalized, "spec normalized"))
    r(_ev(2, ProgressEventKind.narration, "we are working", phase="plan"))
    assert buf.getvalue() == ""


def test_quiet_still_surfaces_failures() -> None:
    r, buf = _renderer(quiet=True)
    r(_ev(9, ProgressEventKind.run_failed, "boom"))
    assert "boom" in buf.getvalue()
    assert "✗" in buf.getvalue()


def test_verbose_includes_data_payload() -> None:
    r, buf = _renderer(verbose=True)
    r(_ev(7, ProgressEventKind.revision_built, "built", data={"build_ok": True}))
    out = buf.getvalue()
    assert "[007]" in out
    assert "revision_built" in out
    assert '"build_ok": true' in out


def test_default_filters_low_signal_events() -> None:
    r, buf = _renderer()
    # ``run_created`` and ``breadcrumb`` are intentionally suppressed in
    # default mode — they're machine markers without operator value.
    r(_ev(0, ProgressEventKind.run_created, "run started"))
    r(_ev(1, ProgressEventKind.breadcrumb, "internal note"))
    assert buf.getvalue() == ""


def test_long_narration_wraps_to_terminal_width(monkeypatch) -> None:
    # Append-only mode must NEVER truncate narrations — terminals can't
    # expand history like the UI can, so the full text has to wrap.
    monkeypatch.setattr(
        "formloop.cli.run_renderer._terminal_width", lambda default=100: 40
    )
    r, buf = _renderer()
    text = "this is a very long narration line that should wrap cleanly across multiple terminal rows"
    r(_ev(1, ProgressEventKind.narration, text, phase="plan"))
    lines = buf.getvalue().rstrip("\n").splitlines()
    # The full text must be reconstructable from the wrapped lines.
    joined = " ".join(line.strip() for line in lines)
    assert text in joined
    # No line should be wildly longer than the configured width — wrapping
    # is best-effort but should keep individual lines bounded.
    assert all(len(line) <= 60 for line in lines), lines
    # And we should produce more than one line for a clearly oversized
    # narration.
    assert len(lines) >= 2


def test_make_renderer_auto_downgrades_when_no_tty() -> None:
    # io.StringIO is not a TTY → rich mode downgrades to plain.
    r, _ = _renderer()
    assert r.options.mode is RendererMode.plain


def test_renderer_finalize_is_safe_to_call_when_no_narration() -> None:
    r, _ = _renderer()
    r.finalize()  # should not raise


def test_renderer_quiet_and_verbose_resolves_to_quiet() -> None:
    r, buf = _renderer(quiet=True, verbose=True)
    r(_ev(1, ProgressEventKind.narration, "trying", phase="plan"))
    # Quiet wins — no narration printed.
    assert buf.getvalue() == ""
