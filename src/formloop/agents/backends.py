from __future__ import annotations

import json
import os
import re
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TypeVar

from agents import Agent, ModelSettings, OpenAIProvider, RunConfig, Runner, set_tracing_disabled
from agents.extensions.models.litellm_provider import LitellmProvider
from openai.types.shared import Reasoning
from pydantic import BaseModel

from formloop.agents.contracts import (
    DesignerOutput,
    EvalJudgeOutput,
    EvalJudgePlan,
    ManagerAssessment,
    ResearchOutput,
    ReviewOutput,
    ReviewPlan,
)
from formloop.config import RunProfile
from formloop.models import NormalizedSpec, ReviewSummary
from formloop.types import ProviderKind, ReviewDecision, ThinkingLevel

OutputT = TypeVar("OutputT", bound=BaseModel)


class LLMBackend(Protocol):
    backend_name: str

    def structured_completion(
        self,
        *,
        role_name: str,
        instructions: str,
        prompt: str,
        output_type: type[OutputT],
        profile: RunProfile,
        trace_metadata: dict[str, str] | None = None,
        image_paths: list[str] | None = None,
    ) -> OutputT: ...


def _thinking_to_reasoning(thinking: ThinkingLevel) -> Reasoning:
    return Reasoning(effort=thinking.value)


@dataclass
class OpenAIAgentsBackend:
    backend_name: str = "openai_agents"

    def _model_provider_for_profile(self, profile: RunProfile):
        if profile.provider == ProviderKind.LITELLM:
            return LitellmProvider()
        return OpenAIProvider(use_responses=True)

    def structured_completion(
        self,
        *,
        role_name: str,
        instructions: str,
        prompt: str,
        output_type: type[OutputT],
        profile: RunProfile,
        trace_metadata: dict[str, str] | None = None,
        image_paths: list[str] | None = None,
    ) -> OutputT:
        model_settings = ModelSettings(
            reasoning=_thinking_to_reasoning(profile.thinking),
            verbosity="low",
        )
        agent = Agent(
            name=role_name,
            instructions=instructions,
            output_type=output_type,
            model=profile.model if profile.provider == ProviderKind.OPENAI_RESPONSES else None,
            model_settings=model_settings,
        )
        tracing_disabled = False
        if profile.provider == ProviderKind.LITELLM and not os.getenv("OPENAI_API_KEY"):
            tracing_disabled = True
            set_tracing_disabled(True)
        run_config = RunConfig(
            model=profile.model if profile.provider == ProviderKind.OPENAI_RESPONSES else None,
            model_provider=self._model_provider_for_profile(profile),
            model_settings=model_settings,
            workflow_name=f"Formloop {role_name}",
            tracing_disabled=tracing_disabled,
            trace_metadata=trace_metadata or {},
        )
        payload: str | list[dict[str, Any]] = prompt
        if image_paths:
            payload = [_text_input_item(prompt), *[_image_input_item(path) for path in image_paths]]
        result = Runner.run_sync(agent, payload, run_config=run_config)
        return result.final_output_as(output_type)


@dataclass
class HeuristicBackend:
    backend_name: str = "heuristic"

    def structured_completion(
        self,
        *,
        role_name: str,
        instructions: str,
        prompt: str,
        output_type: type[OutputT],
        profile: RunProfile,
        trace_metadata: dict[str, str] | None = None,
        image_paths: list[str] | None = None,
    ) -> OutputT:
        if output_type is ManagerAssessment:
            return self._manager(prompt)  # type: ignore[return-value]
        if output_type is ResearchOutput:
            return self._research(prompt)  # type: ignore[return-value]
        if output_type is DesignerOutput:
            return self._designer(prompt)  # type: ignore[return-value]
        if output_type is ReviewPlan:
            return self._review_plan(prompt)  # type: ignore[return-value]
        if output_type is ReviewOutput:
            return self._review_output(prompt)  # type: ignore[return-value]
        if output_type is EvalJudgePlan:
            return self._eval_judge_plan(prompt)  # type: ignore[return-value]
        if output_type is EvalJudgeOutput:
            return self._eval_judge_output(prompt)  # type: ignore[return-value]
        raise ValueError(f"Unsupported output type for heuristic backend: {output_type}")

    def _manager(self, prompt: str) -> ManagerAssessment:
        text = prompt.lower()
        shape = "bracket" if "bracket" in text else "block"
        summary = "Create a CAD model that satisfies the request."
        fit = []
        form = [shape]
        function = []
        constraints = []
        blocking_gaps: list[str] = []
        assumptions: list[str] = []
        research_topics: list[str] = []
        key_dimensions: list[str] = []

        if "mount" in text:
            function.append("support mounting")
        if "m3" in text:
            constraints.append("use M3-compatible features")
            research_topics.append("M3 fastener dimensions and clearances")
        if "bevel gear" in text:
            research_topics.append("bevel gear conventions")
            form.append("gear")
        if "anchor escapement" in text:
            research_topics.append("anchor escapement conventions")
            form.append("escapement")

        width = self._extract_dimension(text, "width")
        height = self._extract_dimension(text, "height")
        depth = self._extract_dimension(text, "depth")
        diameter = self._extract_dimension(text, "diameter")
        thickness = self._extract_dimension(text, "thickness")

        if width:
            key_dimensions.append(f"width={width}mm")
        if height:
            key_dimensions.append(f"height={height}mm")
        if depth:
            key_dimensions.append(f"depth={depth}mm")
        if diameter:
            key_dimensions.append(f"diameter={diameter}mm")
        if thickness:
            key_dimensions.append(f"thickness={thickness}mm")

        if any(word in text for word in ["thing", "something", "part"]) and not function:
            blocking_gaps.append("core function is not specified")
        if "underspecified" in text or "need to decide interface" in text:
            blocking_gaps.append("mandatory interface is unclear")
        if "exact fit" in text and not any(v for v in [width, height, depth, diameter]):
            blocking_gaps.append("must-hit dimensions are missing")

        if not width:
            assumptions.append("Assume width of 40 mm for first-pass design.")
            key_dimensions.append("width=40mm")
        if shape == "block" and not height:
            assumptions.append("Assume height of 20 mm for first-pass design.")
            key_dimensions.append("height=20mm")
        if not depth and shape == "block":
            assumptions.append("Assume depth of 10 mm for first-pass design.")
            key_dimensions.append("depth=10mm")
        if shape == "bracket" and not thickness:
            assumptions.append("Assume bracket thickness of 5 mm.")
            key_dimensions.append("thickness=5mm")

        spec = NormalizedSpec(
            summary=summary,
            fit=fit,
            form=form,
            function=function or ["general purpose mechanical part"],
            constraints=constraints,
            blocking_gaps=blocking_gaps,
            key_dimensions=key_dimensions,
        )
        return ManagerAssessment(
            normalized_spec=spec,
            needs_clarification=bool(blocking_gaps),
            clarification_reason="; ".join(blocking_gaps) if blocking_gaps else None,
            clarification_questions=[f"Please clarify: {gap}." for gap in blocking_gaps],
            assumptions=assumptions if not blocking_gaps else [],
            research_topics=research_topics,
        )

    def _research(self, prompt: str) -> ResearchOutput:
        topic = prompt.splitlines()[0].strip() if prompt.splitlines() else prompt
        topic_lower = prompt.lower()
        findings = []
        citations = []
        if "m3" in topic_lower:
            findings = [
                "Typical M3 clearance holes are approximately 3.2 mm.",
                "Typical M3 tap drill size is approximately 2.5 mm.",
                "Standard M3 hex nut across flats is approximately 5.5 mm.",
            ]
            citations = ["builtin:m3_fastener_basics"]
        elif "bevel gear" in topic_lower:
            findings = [
                "Bevel gears require defined shaft angle, module or pitch, tooth count, and face width.",
                "Pitch cone geometry should be symmetric with mating gear expectations.",
            ]
            citations = ["builtin:bevel_gear_notes"]
        elif "anchor escapement" in topic_lower:
            findings = [
                "Anchor escapements typically require pallet geometry, escape wheel relationship, and locking/drop behavior.",
                "Visual proportions matter as much as named dimensions in early conceptual models.",
            ]
            citations = ["builtin:anchor_escapement_notes"]
        else:
            findings = ["No specialized external research pack found; proceed with explicit assumptions."]
            citations = ["builtin:generic_mechanical_design"]
        return ResearchOutput(topic=topic, findings=findings, citations=citations)

    def _designer(self, prompt: str) -> DesignerOutput:
        text = prompt.lower()
        shape = "bracket" if "bracket" in text else "block"
        dims = {
            "width": self._extract_dimension(text, "width") or 40,
            "height": self._extract_dimension(text, "height") or 20,
            "depth": self._extract_dimension(text, "depth") or 10,
            "thickness": self._extract_dimension(text, "thickness") or 5,
            "hole_diameter": 2.5
            if "undersize holes" in text and "adjust mounting holes to m3 clearance diameter" not in text
            else (self._extract_dimension(text, "m3") or 3.2),
        }
        revision_text = "revise" if "revision instructions" in text else "initial"
        features = ["base solid"]
        if "m3" in text or "mount" in text or shape == "bracket":
            features.append("mounting holes")
        if shape == "bracket":
            features.append("right-angle flange")

        model_source = f'''"""Formloop-generated build123d model."""
# formloop-shape: {shape}
# formloop-dims: {json.dumps(dims, sort_keys=True)}
# formloop-features: {json.dumps(features)}

from build123d import Box, Cylinder, export_step


def build():
    # Placeholder model source for cad-cli integration tests.
    body = Box({dims["width"]}, {dims["height"]}, {dims["depth"]})
    return body


if __name__ == "__main__":
    build()
'''
        rationale = f"{revision_text.capitalize()} {shape} model with dimensions {dims}."
        return DesignerOutput(model_source=model_source, rationale=rationale, expected_features=features)

    def _review_plan(self, prompt: str) -> ReviewPlan:
        requested_measurements = ["bounding_box"]
        requested_feature_checks = []
        lower = prompt.lower()
        if "m3" in lower:
            requested_measurements.append("hole_diameter")
            requested_feature_checks.append("mounting holes present")
        if "reference image" in lower:
            requested_feature_checks.append("reference image comparison")
        return ReviewPlan(
            requested_measurements=requested_measurements,
            requested_feature_checks=requested_feature_checks,
            notes=["Inspect core dimensions before deciding pass or revise."],
        )

    def _review_output(self, prompt: str) -> ReviewOutput:
        decision = ReviewDecision.PASS
        key_findings = ["Model appears to satisfy the normalized spec."]
        suspect_features: list[str] = []
        suspect_dimensions: list[str] = []
        revision_instructions: list[str] = []
        reference_notes: list[str] = []
        lower = prompt.lower()
        if "hole_diameter" in lower and "3.2" not in lower and "3.1" not in lower:
            decision = ReviewDecision.REVISE
            key_findings = ["Mounting hole sizing does not appear M3-compatible."]
            suspect_dimensions.append("hole_diameter")
            revision_instructions.append("Adjust mounting holes to M3 clearance diameter.")
        if "reference image present: true" in lower:
            reference_notes.append("Reference image was included in the review context.")
        summary = ReviewSummary(
            decision=decision,
            confidence=0.82 if decision == ReviewDecision.PASS else 0.64,
            key_findings=key_findings,
            missing_or_suspect_features=suspect_features,
            suspect_dimensions=suspect_dimensions,
            reference_image_notes=reference_notes,
            revision_instructions=revision_instructions,
        )
        return ReviewOutput(summary=summary)

    def _eval_judge_plan(self, prompt: str) -> EvalJudgePlan:
        return EvalJudgePlan(
            requested_measurements=["bounding_box"],
            requested_comparisons=["overall geometry similarity"],
        )

    def _eval_judge_output(self, prompt: str) -> EvalJudgeOutput:
        lower = prompt.lower()
        match = re.search(r'"iou_proxy":\s*([0-9.]+)', lower)
        iou = float(match.group(1)) if match else 0.0
        acceptable = iou >= 0.7
        return EvalJudgeOutput(
            spec_adherence_score=0.9 if acceptable else 0.5,
            dimensional_compliance_score=0.9 if acceptable else 0.45,
            notes=["Heuristic judge completed structured assessment."],
            acceptable=acceptable,
        )

    @staticmethod
    def _extract_dimension(text: str, name: str) -> float | None:
        pattern = rf"{name}[ =:]+(\d+(?:\.\d+)?)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        if name == "m3" and "m3" in text:
            return 3.2
        return None


def _text_input_item(text: str) -> dict[str, Any]:
    return {
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": text,
            }
        ],
    }


def _image_input_item(path: str) -> dict[str, Any]:
    file_path = Path(path)
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    suffix = file_path.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    return {
        "role": "user",
        "content": [
            {
                "type": "input_image",
                "image_url": f"data:image/{mime};base64,{encoded}",
            }
        ],
    }
