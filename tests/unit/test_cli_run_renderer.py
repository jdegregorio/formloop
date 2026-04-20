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


def test_default_mode_suppresses_milestones_shows_narrations() -> None:
    # Post-op-feedback: default mode must NOT print the dim milestone
    # skeleton — only narrations survive in the live feed. Milestones
    # stay in events.jsonl for debugging.
    r, buf = _renderer()
    r(_ev(1, ProgressEventKind.spec_normalized, "spec normalized"))
    r(_ev(2, ProgressEventKind.revision_built, "built", data={"build_ok": True}))
    r(_ev(3, ProgressEventKind.review_completed, "", data={"decision": "pass"}))
    r(_ev(4, ProgressEventKind.narration, "we normalized the spec", phase="plan"))
    out = buf.getvalue()
    assert "spec normalized" not in out
    assert "review" not in out
    assert "we normalized the spec" in out
    assert "›" in out


def test_verbose_mode_shows_milestones_with_indexed_payload() -> None:
    r, buf = _renderer(verbose=True)
    r(
        _ev(
            7,
            ProgressEventKind.revision_built,
            "built",
            data={"build_ok": True, "dimensions": {"overall": "50×50×50 mm"}},
        )
    )
    out = buf.getvalue()
    assert "·" in out  # milestone marker visible
    assert "build=ok" in out
    assert "overall = 50×50×50 mm" in out
    assert "idx=007" in out  # indexed payload footer


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


def test_verbose_trims_floating_point_noise_on_dimensions() -> None:
    # CAD kernels emit values like 50.00000000000001 — render them as
    # 50.0 so the verbose readout stays legible.
    r, buf = _renderer(verbose=True)
    r(
        _ev(
            1,
            ProgressEventKind.revision_built,
            "built",
            data={"build_ok": True, "dimensions": {"width": 50.00000000000001}},
        )
    )
    out = buf.getvalue()
    assert "50.00000000000001" not in out
    assert "width = 50.0" in out


def test_narration_does_not_leak_narration_error_to_user() -> None:
    # Post-op-feedback: the user must not see "(narrator fallback: ...)"
    # — that string is for event logs / debugging only.
    r, buf = _renderer()
    r(
        _ev(
            2,
            ProgressEventKind.narration,
            "we normalized the spec",
            phase="plan",
            narration_error="timeout after 10.0s",
        )
    )
    out = buf.getvalue()
    assert "we normalized the spec" in out
    assert "narrator fallback" not in out
    assert "timeout" not in out


def test_default_filters_low_signal_events() -> None:
    # Default mode prints nothing but narrations and failures: the whole
    # milestone stream stays quiet in the live feed.
    r, buf = _renderer()
    r(_ev(0, ProgressEventKind.run_created, "run started"))
    r(_ev(1, ProgressEventKind.breadcrumb, "internal note"))
    r(_ev(2, ProgressEventKind.spec_normalized, "spec normalized"))
    r(_ev(3, ProgressEventKind.revision_built, "built", data={"build_ok": True}))
    assert buf.getvalue() == ""


def test_narration_continuation_indent_is_constant_across_phases(monkeypatch) -> None:
    # Regression: the continuation indent used to scale with the phase
    # label length, so `[plan]` and `[revision]` wrapped to DIFFERENT
    # columns and the output looked ragged. It must now be fixed.
    monkeypatch.setattr(
        "formloop.cli.run_renderer._terminal_width", lambda default=100: 60
    )
    r, buf = _renderer()
    long_text = (
        "we did a lot of work here and this line is certainly long enough "
        "that it is going to have to wrap at least twice on a 60-column "
        "terminal, which is exactly what we want for this test."
    )
    r(_ev(1, ProgressEventKind.narration, long_text, phase="plan"))
    r(_ev(2, ProgressEventKind.narration, long_text, phase="revision"))
    all_lines = buf.getvalue().rstrip("\n").splitlines()
    # Collect only continuation (non-first) lines for each narration — they
    # start with whitespace and not the `›` marker.
    cont_lines = [line for line in all_lines if line and line[0] == " " and "›" not in line]
    assert cont_lines, "expected continuation lines for a long narration"
    leading = [len(line) - len(line.lstrip(" ")) for line in cont_lines]
    # Every continuation line must share the same indent width.
    assert len(set(leading)) == 1, (leading, cont_lines)


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
