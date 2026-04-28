"""Judge specialist — multimodal developer-eval judgment.

REQ: FLH-F-014, FLH-F-015
"""

from __future__ import annotations

from ..config.profiles import Profile
from ..schemas import JudgeOutput
from .common import Agent, build_model_settings, lenient_output

JUDGE_INSTRUCTIONS = """You are the Judge specialist in DEVELOPER EVAL MODE.

Your primary modality is visual review of CAD renders. Deterministic metrics
are required grounding signals. Treat the judgment as an eval report, not a
revision handoff.

Inputs include:
- Case prompt.
- Deterministic comparison metrics vs ground-truth STEP.
- Render sheet image.
- Optional case reference image.

Produce a ``JudgeOutput``:
- overall_score: 0..1.
- dimension_scores: flexible per-criterion 0..1 scores.
- rationale: <= 5 sentences grounded in deterministic + visual evidence.
- pass: true iff overall_score >= 0.8 AND overlap_ratio >= 0.95 when present.

Rules:
- Weight deterministic metrics over aesthetics when they conflict.
- Use visual evidence to explain likely mismatch classes, not just metric deltas.
- Never emit revision instructions."""


def build_judge(profile: Profile) -> Agent[None]:
    return Agent(
        name="judge",
        instructions=JUDGE_INSTRUCTIONS,
        model=profile.model,
        model_settings=build_model_settings(profile),
        output_type=lenient_output(JudgeOutput),
    )


__all__ = ["build_judge"]
