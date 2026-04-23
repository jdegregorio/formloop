from __future__ import annotations

import json
from pathlib import Path

from ..agents import PromptContext
from ..schemas import ProgressEventKind, RevisionTrigger, ReviewDecision
from ..store.run_store import CandidateBundle
from .narration import fallback_revision_built
from .phase_context import OrchestrationPhaseContext, PhaseRuntimeContext
from .review import review_phase


def _staging_views_dir(run_root: Path, attempt: int) -> Path:
    out = run_root / "_work" / f"views_{attempt:03d}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _stage_views(render_out: Path, staging: Path) -> list[Path]:
    names = ("front", "back", "left", "right", "top", "bottom", "iso")
    staged: list[Path] = []
    for name in names:
        src = render_out / f"{name}.png"
        if src.is_file():
            dst = staging / src.name
            dst.write_bytes(src.read_bytes())
            staged.append(dst)
    return staged


def _write_inspect_json(run_root: Path, attempt: int, payload: dict | None) -> Path | None:
    if not payload:
        return None
    path = run_root / "_work" / f"inspect_{attempt:03d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return path


async def revision_loop_phase(
    ctx: OrchestrationPhaseContext,
    runtime: PhaseRuntimeContext,
    *,
    plan,
    findings: list[dict],
    max_revisions: int,
) -> str | None:
    run = runtime.run
    prior_review: dict | None = None
    delivered: str | None = None

    for attempt in range(1, max_revisions + 1):
        ctx.emit(
            run.run_name,
            ProgressEventKind.revision_started,
            message=f"revision attempt {attempt}",
            data={"attempt": attempt},
        )
        if prior_review is not None:
            await ctx.narrate(
                run.run_name,
                phase="revision",
                just_completed="read the reviewer's feedback",
                next_step=f"produce revision attempt {attempt}",
                why="",
                signals={"attempt": attempt, "max_attempts": max_revisions},
                context={
                    "prior_decision": prior_review.get("decision"),
                    "prior_key_findings": (prior_review.get("key_findings") or [])[:3],
                    "revision_instructions": (prior_review.get("revision_instructions") or [])[:3],
                },
                fallback=f"starting revision attempt {attempt}",
            )
        prompt_ctx = PromptContext(
            input_summary=runtime.user_prompt,
            current_spec=plan.normalized_spec.model_dump(),
            assumptions=[{"topic": a.topic, "assumption": a.assumption} for a in plan.assumptions],
            research_findings=findings,
            prior_review=prior_review,
        )
        designer_input = (
            f"Design brief:\n{plan.design_brief}\n\n"
            f"Context (JSON):\n{prompt_ctx.to_prompt_text()}\n\n"
            "Author model.py, build, inspect, render, then return CadRevisionResult."
        )
        cad_out = await ctx.design_revision(designer_input, runtime.run_ctx, runtime.profile)
        ctx.emit(
            run.run_name,
            ProgressEventKind.revision_built,
            message=f"designer returned build_ok={cad_out.build_ok} render_ok={cad_out.render_ok}",
            data={
                "build_ok": cad_out.build_ok,
                "inspect_ok": cad_out.inspect_ok,
                "render_ok": cad_out.render_ok,
                "dimensions": cad_out.dimensions,
            },
        )
        await ctx.narrate(
            run.run_name,
            phase="revision",
            just_completed="finished the CAD build and render",
            next_step=("send it to review" if cad_out.build_ok and cad_out.render_ok else "retry because the build or render failed"),
            why="",
            signals={
                "attempt": attempt,
                "build_ok": cad_out.build_ok,
                "render_ok": cad_out.render_ok,
                "inspect_ok": cad_out.inspect_ok,
            },
            context={
                "revision_notes": (cad_out.revision_notes or "")[:280],
                "dimensions": dict(cad_out.dimensions or {}),
                "known_risks": list(cad_out.known_risks or [])[:3],
                "build_errors": list(cad_out.build_errors or [])[:2],
            },
            fallback=fallback_revision_built(cad_out),
        )

        if not (
            cad_out.build_ok
            and cad_out.render_ok
            and runtime.run_ctx.notes.get("last_build")
            and runtime.run_ctx.notes.get("last_render")
        ):
            ctx.emit(
                run.run_name,
                ProgressEventKind.breadcrumb,
                message="no full bundle this attempt; not persisting",
                data={"attempt": attempt, "build_errors": cad_out.build_errors[:3]},
            )
            if attempt >= max_revisions:
                break
            prior_review = {
                "decision": "revise",
                "revision_instructions": [
                    "Previous attempt did not produce a full build+render bundle.",
                    f"Errors: {cad_out.build_errors[:3]}",
                ],
            }
            continue

        build_dir = Path(runtime.run_ctx.notes["last_build"]["output_dir"])
        render_dir = Path(runtime.run_ctx.notes["last_render"]["output_dir"])
        staging = _staging_views_dir(runtime.run_root, attempt)
        _stage_views(render_dir, staging)

        build_meta = build_dir / "build-metadata.json"
        render_meta = render_dir / "render-metadata.json"
        inspect_src = _write_inspect_json(runtime.run_root, attempt, runtime.run_ctx.notes.get("last_inspect"))

        bundle = CandidateBundle(
            trigger=RevisionTrigger.initial if attempt == 1 else RevisionTrigger.review_revise,
            spec_snapshot=plan.normalized_spec.model_dump(),
            designer_notes=cad_out.revision_notes,
            known_risks=list(cad_out.known_risks),
            model_py_src=runtime.run_ctx.source_dir / "model.py",
            step_src=build_dir / "model.step",
            glb_src=build_dir / "model.glb",
            views_dir_src=staging,
            render_sheet_src=render_dir / "sheet.png",
            build_metadata_src=build_meta if build_meta.is_file() else None,
            render_metadata_src=render_meta if render_meta.is_file() else None,
            inspect_summary_src=inspect_src,
        )
        fresh = ctx.load_run(run.run_name)
        revision, _ = ctx.persist_revision(fresh, bundle)
        delivered = revision.revision_name
        ctx.emit(
            run.run_name,
            ProgressEventKind.revision_persisted,
            message=f"persisted {revision.revision_name}",
            data={"revision": revision.revision_name, "ordinal": revision.ordinal},
        )

        review = await review_phase(
            ctx,
            runtime,
            plan=plan,
            cad_out=cad_out,
            revision=revision,
        )
        if review.decision == ReviewDecision.pass_:
            ctx.emit(run.run_name, ProgressEventKind.breadcrumb, message="revision accepted")
            break
        prior_review = review.model_dump()

    return delivered
