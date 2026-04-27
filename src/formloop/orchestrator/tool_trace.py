"""Lightweight agent tool-call tracing."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import RunHooks

SNIPPET_CHARS = 4000


def _clip(value: Any) -> Any:
    if isinstance(value, str) and len(value) > SNIPPET_CHARS:
        return value[:SNIPPET_CHARS] + "\n...[truncated]"
    return value


def _dump_raw(raw: Any) -> dict[str, Any]:
    if hasattr(raw, "model_dump"):
        return raw.model_dump(exclude_unset=True)
    if isinstance(raw, dict):
        return dict(raw)
    payload: dict[str, Any] = {}
    for attr in ("type", "name", "arguments", "call_id", "id"):
        if hasattr(raw, attr):
            payload[attr] = getattr(raw, attr)
    return payload


def _parse_arguments(raw_args: Any) -> Any:
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args)
        except json.JSONDecodeError:
            return raw_args
    return raw_args


def _tool_name(payload: dict[str, Any]) -> str:
    if payload.get("name"):
        return str(payload["name"])
    if payload.get("type") == "apply_patch_call":
        return "apply_patch"
    return str(payload.get("type") or "unknown_tool")


@dataclass
class AgentToolTraceRecorder(RunHooks):
    """Collect a compact tool trace for one agent run."""

    agent_name: str
    model: str
    reasoning: str
    max_turns: int
    started_tools: list[str] = field(default_factory=list)

    async def on_tool_start(self, context, agent, tool) -> None:  # type: ignore[override]
        self.started_tools.append(getattr(tool, "name", tool.__class__.__name__))

    def _base_trace(self, calls: list[dict[str, Any]]) -> dict[str, Any]:
        counts = Counter(call["tool"] for call in calls)
        return {
            "agent": self.agent_name,
            "model": self.model,
            "reasoning": self.reasoning,
            "max_turns": self.max_turns,
            "total_tool_calls": len(calls),
            "counts": dict(sorted(counts.items())),
            "calls": calls,
        }

    def trace_from_result(self, result: Any) -> dict[str, Any]:
        outputs_by_call_id: dict[str, Any] = {}
        calls: list[dict[str, Any]] = []
        for item in getattr(result, "new_items", []) or []:
            item_type = getattr(item, "type", "")
            payload = _dump_raw(getattr(item, "raw_item", {}))
            if item_type == "tool_call_output_item":
                call_id = payload.get("call_id")
                if call_id:
                    outputs_by_call_id[str(call_id)] = _clip(getattr(item, "output", None))
                continue
            if item_type != "tool_call_item":
                continue
            call_id = payload.get("call_id") or payload.get("id")
            calls.append(
                {
                    "tool": _tool_name(payload),
                    "arguments": _parse_arguments(payload.get("arguments") or payload.get("input")),
                    "call_id": str(call_id) if call_id else None,
                    "raw_type": payload.get("type"),
                }
            )
        for call in calls:
            call_id = call.get("call_id")
            if call_id in outputs_by_call_id:
                call["output"] = outputs_by_call_id[call_id]
        return self._base_trace(calls)

    def trace_from_error(self, exc: BaseException) -> dict[str, Any]:
        trace = self._base_trace(
            [
                {"tool": tool_name, "arguments": None, "call_id": None, "raw_type": "hook_start"}
                for tool_name in self.started_tools
            ]
        )
        trace["error_type"] = type(exc).__name__
        trace["error"] = str(exc)[:1000]
        trace["partial"] = True
        return trace


def write_tool_trace(path: Path, trace: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
