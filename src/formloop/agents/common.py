"""Shared helpers for OpenAI Agents SDK integration."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar, cast

from agents import ModelSettings, RunHooks
from agents.result import RunResult, RunResultStreaming

ModelT = TypeVar("ModelT")


@dataclass(slots=True)
class HarnessAgentContext:
    run_id: str
    trace_events: list[dict[str, Any]] = field(default_factory=list)


class ExecutionTraceHooks(RunHooks[HarnessAgentContext]):
    """Collect a sanitized local execution trace for each run."""

    # Req: FLH-F-011, FLH-NF-007

    async def on_agent_start(self, context: Any, agent: Any) -> None:
        context.context.trace_events.append({"type": "agent_start", "agent": agent.name})

    async def on_agent_end(self, context: Any, agent: Any, output: Any) -> None:
        context.context.trace_events.append({"type": "agent_end", "agent": agent.name})

    async def on_tool_start(self, context: Any, agent: Any, tool: Any) -> None:
        context.context.trace_events.append(
            {"type": "tool_start", "agent": agent.name, "tool": getattr(tool, "name", str(tool))}
        )

    async def on_tool_end(self, context: Any, agent: Any, tool: Any, result: Any) -> None:
        context.context.trace_events.append(
            {"type": "tool_end", "agent": agent.name, "tool": getattr(tool, "name", str(tool))}
        )

    async def on_llm_end(self, context: Any, agent: Any, response: Any) -> None:
        context.context.trace_events.append({"type": "llm_end", "agent": agent.name})


def reasoning_settings(reasoning: str, *, tool_choice: str | None = None) -> ModelSettings:
    return ModelSettings(
        reasoning=cast(Any, {"effort": reasoning}),
        tool_choice=tool_choice,
        parallel_tool_calls=False,
    )


def data_url_for_image(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    suffix = path.suffix.lower().removeprefix(".") or "png"
    return f"data:image/{suffix};base64,{encoded}"


def text_input_item(text: str) -> dict[str, Any]:
    return {"type": "input_text", "text": text}


def image_input_item(path: Path) -> dict[str, Any]:
    return {"type": "input_image", "image_url": data_url_for_image(path)}


def user_message(*content_items: dict[str, Any]) -> dict[str, Any]:
    return {"role": "user", "content": list(content_items)}


async def json_output_extractor(result: RunResult | RunResultStreaming) -> str:
    output = result.final_output
    if hasattr(output, "model_dump_json"):
        return cast(str, output.model_dump_json())
    return json.dumps(output)
