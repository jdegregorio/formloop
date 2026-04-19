from __future__ import annotations

from formloop.runtime.source_validation import validate_cad_source


def test_flh_v_001_accepts_minimal_build123d_source() -> None:
    result = validate_cad_source(
        "from build123d import Box\n\n"
        "def build_model(params, context):\n"
        "    return Box(10, 10, 10)\n"
    )
    assert result.ok
    assert result.errors == []


def test_flh_v_001_rejects_banned_imports_and_calls() -> None:
    result = validate_cad_source(
        "import os\n\ndef build_model(params, context):\n    os.system('whoami')\n    return None\n"
    )
    assert not result.ok
    assert any("not allowed" in error for error in result.errors)


def test_flh_v_001_rejects_unsupported_primitive_keyword_args() -> None:
    result = validate_cad_source(
        "from build123d import Box, Pos\n\n"
        "def build_model(params, context):\n"
        "    return Box(10, 10, 10, pos=Pos(0, 0, 0))\n"
    )
    assert not result.ok
    assert any("keyword argument" in error for error in result.errors)
