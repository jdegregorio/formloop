from __future__ import annotations

import json
from types import SimpleNamespace

from formloop.orchestrator.tool_trace import AgentToolTraceRecorder, write_tool_trace


def _item(item_type: str, raw_item, output=None):
    return SimpleNamespace(type=item_type, raw_item=raw_item, output=output)


def test_tool_trace_recorder_counts_tools_and_arguments(tmp_path) -> None:
    recorder = AgentToolTraceRecorder(
        agent_name="cad_designer",
        model="gpt-test",
        reasoning="low",
        max_turns=20,
    )
    result = SimpleNamespace(
        new_items=[
            _item(
                "tool_call_item",
                SimpleNamespace(
                    type="function_call",
                    name="python_inspect",
                    arguments='{"target":"build123d.Box"}',
                    call_id="call-1",
                ),
            ),
            _item(
                "tool_call_output_item",
                {"type": "function_call_output", "call_id": "call-1"},
                output="signature...",
            ),
            _item(
                "tool_call_item",
                {"type": "apply_patch_call", "input": {"path": "model.py"}, "call_id": "call-2"},
            ),
        ]
    )

    trace = recorder.trace_from_result(result)
    assert trace["total_tool_calls"] == 2
    assert trace["counts"] == {"apply_patch": 1, "python_inspect": 1}
    assert trace["calls"][0]["arguments"] == {"target": "build123d.Box"}
    assert trace["calls"][0]["output"] == "signature..."
    assert trace["calls"][1]["arguments"] == {"path": "model.py"}

    path = tmp_path / "trace.json"
    write_tool_trace(path, trace)
    assert json.loads(path.read_text())["counts"] == trace["counts"]


def test_tool_trace_recorder_writes_partial_error_trace() -> None:
    recorder = AgentToolTraceRecorder(
        agent_name="cad_designer",
        model="gpt-test",
        reasoning="low",
        max_turns=20,
    )
    recorder.started_tools.extend(["python_inspect", "python_inspect"])

    trace = recorder.trace_from_error(TimeoutError("ran out of turns"))

    assert trace["partial"] is True
    assert trace["error_type"] == "TimeoutError"
    assert trace["total_tool_calls"] == 2
    assert trace["counts"] == {"python_inspect": 2}
