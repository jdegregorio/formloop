from __future__ import annotations

import logging
from pathlib import Path

from ..schemas import ProgressEventKind, ReviewDecision
from ..sdk_messages import build_single_user_multimodal_message
from .narration import fallback_review
from .phase_context import OrchestrationPhaseContext, PhaseRuntimeContext

logger = logging.getLogger(__name__)


def _read_source_excerpt(path: Path, *, max_chars: int = 20000) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n# [truncated]"


async def review_phase(
    ctx: OrchestrationPhaseContext,
    runtime: PhaseRuntimeContext,
    *,
    plan,
    cad_out,
    revision,
):
    run = runtime.run
    logger.info("review phase: start revision=%s", revision.revision_name)
    ctx.emit(
        run.run_name,
        ProgressEventKind.review_started,
        message=f"reviewing {revision.revision_name}",
    )
    payload = {
        "spec": plan.normalized_spec.model_dump(),
        "designer_notes": cad_out.revision_notes,
        "designer_dimensions": cad_out.dimensions,
        "known_risks": cad_out.known_risks,
        "inspect_summary": runtime.run_ctx.notes.get("last_inspect"),
        "model_source": _read_source_excerpt(runtime.run_ctx.source_dir / "model.py"),
        "review_focus": {
            "primary_modality": "visual",
            "required_images": ["render_sheet", "reference_image_if_present"],
            "summary_style": (
                "Return one concise summary, one clear next_step, and brief key_findings."
            ),
        },
    }
    sheet_path = runtime.run_root / "revisions" / revision.revision_name / "render-sheet.png"
    image_paths = [sheet_path]
    if run.reference_image:
        image_paths.append(Path(run.reference_image))
    review = await ctx.review_revision(
        build_single_user_multimodal_message(
            lead_text="Review this revision and produce a ReviewSummary.",
            payload=payload,
            image_paths=image_paths,
        ),
        runtime.profile_for("reviewer"),
    )
    fresh = ctx.load_run(run.run_name)
    ctx.attach_review(fresh, revision.revision_name, review)
    logger.info(
        "review decision: revision=%s decision=%s outcome=%s",
        revision.revision_name,
        review.decision.value,
        review.outcome.value,
    )
    ctx.emit(
        run.run_name,
        ProgressEventKind.review_completed,
        message=f"review outcome: {review.outcome.value}",
        data={
            "revision": revision.revision_name,
            "decision": review.decision.value,
            "outcome": review.outcome.value,
            "summary": review.summary,
            "next_step": review.next_step,
        },
    )
    await ctx.narrate(
        run.run_name,
        phase="review",
        just_completed="finished the review",
        next_step=(
            "deliver this design"
            if review.decision == ReviewDecision.pass_
            else "iterate on the design"
        ),
        why="",
        signals={"decision": review.decision.value, "outcome": review.outcome.value},
        context={
            "decision": review.decision.value,
            "outcome": review.outcome.value,
            "summary": review.summary,
            "next_step": review.next_step,
            "key_findings": list(review.key_findings or [])[:4],
            "revision_instructions": (
                [review.revision_instructions] if review.revision_instructions else []
            ),
        },
        fallback=fallback_review(review),
    )
    return review
