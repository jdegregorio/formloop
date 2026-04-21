"""Unit tests: CAD Designer knowledge + DesignPlan integration.

REQ: FLH-F-028, FLH-F-029, FLH-D-026
"""

from __future__ import annotations

import pytest

from formloop.agents import CadRevisionResult, DesignPlan, build_cad_designer
from formloop.agents.cad_designer import _INSTRUCTIONS_TEMPLATE, _build_instructions
from formloop.config.profiles import Profile


@pytest.fixture()
def profile() -> Profile:
    return Profile(name="dev_test", model="gpt-5.4-nano", reasoning="low")


def test_instructions_demand_planning_first() -> None:
    text = _build_instructions()
    # The mandatory planning step is explicit in the scaffold.
    assert "PLAN" in text
    assert "paradigm" in text
    assert "DesignPlan" in text


def test_instructions_mention_lookup_tool() -> None:
    text = _build_instructions()
    assert "build123d_lookup" in text


def test_instructions_name_each_external_library() -> None:
    text = _build_instructions()
    for lib in ("bd_warehouse", "bd_vslot", "py_gearworks", "bd_beams_and_bars"):
        assert lib in text, f"missing external-lib mention: {lib}"


def test_instructions_warn_about_fresh_interpreter() -> None:
    # Agent must not assume REPL-style state retention between turns.
    text = _build_instructions()
    assert "fresh Python interpreter" in text


def test_instructions_bias_external_libs_for_trigger_words() -> None:
    # The lookup step must name each trigger category so the designer knows
    # when to reach for the specialized library instead of rolling its own.
    text = _build_instructions()
    # threaded-fastener bias → bd_warehouse
    assert "thread" in text.lower() and "bd_warehouse" in text
    # gear bias → py_gearworks
    assert "gear" in text.lower() and "py_gearworks" in text
    # v-slot bias → bd_vslot
    assert "v-slot" in text.lower() and "bd_vslot" in text
    # beam bias → bd_beams_and_bars
    assert ("beam" in text.lower() or "i-beam" in text.lower()) and "bd_beams_and_bars" in text
    # And the framing must be *preference*, not "only when necessary".
    assert "prefer" in text.lower() or "Prefer" in text


def test_instructions_are_within_size_budget() -> None:
    # Static INSTRUCTIONS base + inlined cheat-sheet slice. Keep bounded so
    # per-call token cost stays predictable. Budget chosen to match the
    # feature plan (~3k tokens ≈ 12k chars for the cheat slice + ~2k chars
    # template overhead).
    text = _build_instructions()
    assert len(text) <= 16000, f"INSTRUCTIONS grew to {len(text)} chars"


def test_template_is_stable_without_knowledge_pack() -> None:
    # Even without a cheat-sheet slice, the template must still spell out
    # the planning step and the lookup tool.
    assert "PLAN" in _INSTRUCTIONS_TEMPLATE
    assert "build123d_lookup" in _INSTRUCTIONS_TEMPLATE


def test_design_plan_round_trip() -> None:
    dp = DesignPlan(
        paradigm="mixed",
        paradigm_rationale="sketch-extrude for the base, algebra for the finish",
        primary_primitives=["BuildSketch", "extrude", "Cylinder"],
        external_libs_used=["bd_warehouse"],
        decomposition=[
            "sketch the base profile",
            "extrude to 20 mm",
            "subtract threaded M6 hole",
        ],
        open_questions=["corner fillet radius not specified"],
    )
    js = dp.model_dump_json()
    restored = DesignPlan.model_validate_json(js)
    assert restored == dp


def test_design_plan_requires_decomposition() -> None:
    # Empty decomposition is a planning failure — the schema must reject it
    # so the model produces at least one bullet.
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DesignPlan(
            paradigm="algebra",
            paradigm_rationale="simple",
            decomposition=[],
        )


def test_cad_revision_result_requires_design_plan() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CadRevisionResult(
            model_py_written=True,
            build_ok=True,
            inspect_ok=True,
            render_ok=True,
            revision_notes="missing plan",
        )


def test_lookup_tool_registered_on_designer(profile: Profile) -> None:
    agent = build_cad_designer(profile)
    tool_names = {getattr(t, "name", t.__class__.__name__) for t in agent.tools}
    assert "build123d_lookup" in tool_names


def test_external_lib_prelude_routes_on_trigger_keywords() -> None:
    from formloop.agents.cad_designer import _external_lib_prelude

    # threads → bd_warehouse import block + rationale
    p = _external_lib_prelude("M12 threaded rod")
    assert "bd_warehouse.thread" in p
    assert "IsoThread" in p
    assert "hand-loft" in p  # rationale phrase

    # gears → py_gearworks
    p = _external_lib_prelude("helical gear 30 teeth")
    assert "py_gearworks" in p
    assert "HelicalGear" in p or "SpurGear" in p

    # v-slot → bd_vslot
    p = _external_lib_prelude("20x20 aluminum extrusion")
    assert "bd_vslot" in p
    assert "VSlot" in p

    # beams → bd_beams_and_bars + version warning
    p = _external_lib_prelude("I-beam IPN 100")
    assert "bd_beams_and_bars" in p
    assert "3.13" in p

    # unrelated topic → no prelude
    assert _external_lib_prelude("fillet edges") == ""
    assert _external_lib_prelude("topology selection") == ""
