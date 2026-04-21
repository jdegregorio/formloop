"""library_primer_for — high-priority routing hints for the CAD Designer.

REQ: FLH-F-003, FLH-F-028 — when a prompt mentions specialized features
(threads, gears, v-slot extrusions, structural beams), the designer must be
pushed toward the matching Build123D ecosystem library rather than rolling
the geometry by hand. Static INSTRUCTIONS alone proved insufficient (every
gear test skipped py_gearworks) — the fix injects a per-prompt primer into
the user input where the model pays the most attention.
"""

from __future__ import annotations

import pytest

from formloop.agents.cad_designer import library_primer_for


def test_empty_when_no_trigger_matches() -> None:
    assert library_primer_for("a plain 20mm cube") == ""
    assert library_primer_for("") == ""
    assert library_primer_for("rectangular plate with two 6mm holes") == ""


@pytest.mark.parametrize(
    "prompt,expect_module",
    [
        ("a 20-tooth involute spur gear, module 2", "py_gearworks"),
        ("design a helical gear with 30 teeth", "py_gearworks"),
        ("rack and pinion assembly", "py_gearworks"),
        ("M8 threaded rod 60mm long", "bd_warehouse"),
        ("tapped blind hole M6 with 12mm depth", "bd_warehouse"),
        ("a hex bolt, a flange, and a bearing", "bd_warehouse"),
        ("a 300mm length of 20x20 v-slot extrusion", "bd_vslot"),
        ("aluminum extrusion 20x40", "bd_vslot"),
        ("UPN80 structural steel channel, 500mm long", "bd_beams_and_bars"),
        ("an I-beam 1m long", "bd_beams_and_bars"),
    ],
)
def test_primer_emitted_for_trigger(prompt: str, expect_module: str) -> None:
    primer = library_primer_for(prompt)
    assert primer, f"expected a primer for prompt {prompt!r}"
    assert "HIGH-PRIORITY LIBRARY ROUTING" in primer
    # The primer must contain a paste-ready import referencing the module
    # so the model sees a concrete entry point, not just advice.
    assert expect_module in primer
    # Escape hatch clause should also appear so the agent knows the default
    # is to USE the lib, but can justify an alternative in paradigm_rationale.
    assert "paradigm_rationale" in primer


def test_case_insensitive() -> None:
    assert library_primer_for("HELICAL GEAR, 30 teeth") != ""
    assert library_primer_for("M8 THREADED rod") != ""


def test_combined_triggers_produce_multiple_blocks() -> None:
    """A spec that mentions threads AND gears should primer both libs."""

    primer = library_primer_for(
        "a gearbox with an M10 threaded output shaft and an involute gear"
    )
    assert "py_gearworks" in primer
    assert "bd_warehouse" in primer
    # Each block gets its own "Library primer" header line.
    assert primer.count("Library primer") >= 2


def test_primer_quotes_the_matched_trigger() -> None:
    """The primer should tell the designer which trigger word fired."""

    primer = library_primer_for("a small spur gear with 15 teeth")
    # The matched trigger ('gear', 'spur', …) should appear quoted in the
    # header so the designer understands why this routing was suggested.
    assert "'gear'" in primer or "'spur'" in primer


def test_primer_includes_code_fence() -> None:
    primer = library_primer_for("M8 threaded rod")
    # The snippet must be in a ```python block so the model picks it up as
    # executable code rather than prose.
    assert "```python" in primer
    assert "```" in primer.split("```python", 1)[1]
