"""Header / footer formatting for ``formloop run``.

REQ: FLH-F-027
"""

from __future__ import annotations

import io
from pathlib import Path

from formloop.cli.run_report import print_run_footer, print_run_header


def test_header_includes_request_profile_and_model() -> None:
    buf = io.StringIO()
    print_run_header(
        prompt="a 20mm cube with chamfered edges",
        profile_name="dev_test",
        model="gpt-5.4-nano",
        color=False,
        stream=buf,
    )
    out = buf.getvalue()
    assert "formloop run" in out
    assert "dev_test" in out
    assert "gpt-5.4-nano" in out
    assert "a 20mm cube with chamfered edges" in out


def test_header_wraps_long_prompt() -> None:
    buf = io.StringIO()
    long_prompt = (
        "a 50mm x 50mm x 50mm cube with rounded r5 edges and three through-holes "
        "of 35mm diameter centered on each principal axis"
    )
    print_run_header(
        prompt=long_prompt,
        profile_name="normal",
        model="gpt-5.4",
        color=False,
        stream=buf,
    )
    out = buf.getvalue()
    # All prompt content is preserved.
    assert "rounded r5 edges" in out
    assert "principal axis" in out


def test_footer_succeeded_shows_artifacts_and_summary() -> None:
    buf = io.StringIO()
    print_run_footer(
        run_name="run-0042",
        status="succeeded",
        delivered_revision="rev-001",
        artifacts_dir=Path("/tmp/var/runs/run-0042/revisions/rev-001"),
        final_answer="A 20mm cube was produced with the requested chamfer.",
        color=False,
        stream=buf,
    )
    out = buf.getvalue()
    assert "✓" in out
    assert "succeeded" in out
    assert "run-0042" in out
    assert "rev-001" in out
    assert "/tmp/var/runs/run-0042/revisions/rev-001" in out
    assert "Summary" in out
    assert "20mm cube was produced" in out


def test_footer_failed_marks_status_and_skips_missing_fields() -> None:
    buf = io.StringIO()
    print_run_footer(
        run_name="run-0099",
        status="failed",
        delivered_revision=None,
        artifacts_dir=None,
        final_answer=None,
        color=False,
        stream=buf,
    )
    out = buf.getvalue()
    assert "✗" in out
    assert "failed" in out
    assert "run-0099" in out
    # No delivered revision / summary blocks when there's nothing to show.
    assert "Delivered revision" not in out
    assert "Summary" not in out
