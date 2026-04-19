from __future__ import annotations

from formloop.dev.traceability import build_traceability_report


def test_traceability_report_flags_remaining_gaps_but_tracks_core_requirements() -> None:
    report = build_traceability_report()
    assert report["total_requirements"] > 0
    references = report["references"]
    assert "FLH-D-020" in references
    assert "FLH-F-013" in references
