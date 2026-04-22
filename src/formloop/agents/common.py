"""Shared agent primitives.

REQ: FLH-D-010, FLH-D-013, FLH-D-017

Centralizes the openai-agents SDK imports so future SDK drift is fixed in a
single module, and defines the RunContext / PromptContext separation (the
harness keeps filesystem/identity details out of LLM inputs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# SDK surface ---------------------------------------------------------------
from agents import (  # noqa: F401 -- re-exported for the rest of the package
    Agent,
    AgentOutputSchema,
    ModelSettings,
    RunContextWrapper,
    Runner,
    WebSearchTool,
    function_tool,
)
from openai.types.shared import Reasoning

from ..config.profiles import Profile
from ..schemas import AssumptionRecord


def build_model_settings(profile: Profile) -> ModelSettings:
    """ModelSettings for a resolved profile (FLH-D-017)."""

    return ModelSettings(reasoning=Reasoning(effort=profile.reasoning))


def lenient_output(model_cls: type) -> AgentOutputSchema:
    """Wrap a Pydantic model as a non-strict AgentOutputSchema.

    Our Pydantic contracts use untyped dicts (for spec_snapshot etc.), which
    the Agents SDK rejects under strict JSON Schema. Non-strict mode lets
    these through — acceptable since we validate the result with Pydantic.
    """

    return AgentOutputSchema(model_cls, strict_json_schema=False)


@dataclass
class RunContext:
    """Internal state threaded through agent tool calls.

    This object is the ``context`` argument on ``Runner.run`` and is exposed
    to tools via ``RunContextWrapper``. It MUST NOT be serialized into the
    model input — prompt content is built separately via ``PromptContext``
    (FLH-D-013).
    """

    run_name: str
    run_root: Path
    source_dir: Path
    profile: Profile
    assumptions: list[AssumptionRecord] = field(default_factory=list)
    research_topics: list[str] = field(default_factory=list)
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptContext:
    """Sanitized slice of state that the agent may see.

    Only high-level intent belongs here — no absolute paths, no uuids, no
    internal identifiers.
    """

    input_summary: str
    current_spec: dict[str, Any]
    assumptions: list[dict[str, str]]
    research_findings: list[dict[str, Any]]
    prior_review: dict[str, Any] | None = None
    reference_image_caption: str | None = None

    def to_prompt_text(self) -> str:
        import json

        payload = {
            "input_summary": self.input_summary,
            "current_spec": self.current_spec,
            "assumptions": self.assumptions,
            "research_findings": self.research_findings,
            "prior_review": self.prior_review,
            "reference_image_caption": self.reference_image_caption,
        }
        return json.dumps(payload, indent=2)


__all__ = [
    "Agent",
    "AgentOutputSchema",
    "ModelSettings",
    "PromptContext",
    "Reasoning",
    "RunContext",
    "RunContextWrapper",
    "Runner",
    "WebSearchTool",
    "build_model_settings",
    "function_tool",
    "lenient_output",
]
