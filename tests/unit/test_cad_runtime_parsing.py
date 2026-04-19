from __future__ import annotations

from formloop.runtime.cad import CadCliRuntime


def test_flh_d_020_parses_json_from_mixed_stdout() -> None:
    runtime = CadCliRuntime()
    payload = runtime._parse_json_stdout('noise before\n{\n  "status": "ok"\n}\n')
    assert payload == {"status": "ok"}
