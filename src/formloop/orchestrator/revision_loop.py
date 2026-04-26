from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..agents import PromptContext
from ..agents.cad_designer import CadRevisionResult, CadSourceResult
from ..runtime.cad_cli import (
    CadBuildResult,
    CadInspectResult,
    CadRenderResult,
    cad_build,
    cad_inspect_summary,
    cad_render,
)

from ..runtime.subprocess import CliError
from ..schemas import ProgressEventKind, ReviewDecision, RevisionTrigger
from ..store.run_store import CandidateBundle
from .narration import fallback_revision_built
from .phase_context import OrchestrationPhaseContext, PhaseRuntimeContext
from .review import review_phase

logger = logging.getLogger(__name__)

MAX_SOURCE_DEBUG_LOOPS = 3
MAX_SOURCE_ATTEMPTS = 1 + MAX_SOURCE_DEBUG_LOOPS
SNIPPET_CHARS = 4000


class CadCommandEvidence(BaseModel):
    command: str
    status: str
    duration_s: float
    timeout_s: float | None = None
    returncode: int | None = None
    summary: str = ""
    stdout_snippet: str = ""
    stderr_snippet: str = ""
    error_type: str | None = None
    output_dir: str | None = None
    metadata_path: str | None = None


class CadFailureFeedback(BaseModel):
    revision_attempt: int
    source_attempt: int
    failed_phase: str
    failed_command: str
    summary: str
    detail: str
    returncode: int | None = None
    stdout_snippet: str = ""
    stderr_snippet: str = ""
    timeout_s: float | None = None
    elapsed_s: float | None = None
    debug_artifact_path: str
    repair_instructions: list[str] = Field(default_factory=list)


class CadValidationResult(BaseModel):
    ok: bool
    revision_attempt: int
    source_attempt: int
    debug_dir: str
    source_path: str
    build_ok: bool = False
    inspect_ok: bool = False
    render_ok: bool = False
    commands: list[CadCommandEvidence] = Field(default_factory=list)
    failure_feedback: CadFailureFeedback | None = None
    build_result: dict[str, Any] | None = None
    inspect_result: dict[str, Any] | None = None
    render_result: dict[str, Any] | None = None


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


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def _clip(text: str | None) -> str:
    text = text or ""
    if len(text) <= SNIPPET_CHARS:
        return text
    return text[:SNIPPET_CHARS] + "\n...[truncated]"


def _next_source_attempt_dir(run_root: Path) -> tuple[int, Path]:
    root = run_root / "_work" / "source_attempts"
    root.mkdir(parents=True, exist_ok=True)
    existing: list[int] = []
    for path in root.glob("attempt-*"):
        suffix = path.name.removeprefix("attempt-")
        if suffix.isdigit():
            existing.append(int(suffix))
    ordinal = (max(existing) if existing else 0) + 1
    attempt_dir = root / f"attempt-{ordinal:03d}"
    attempt_dir.mkdir(parents=True, exist_ok=False)
    return ordinal, attempt_dir


def _format_designer_input(
    *,
    plan,
    runtime: PhaseRuntimeContext,
    findings: list[dict],
    prior_review: dict | None,
    failure_feedback: CadFailureFeedback | None,
) -> str:
    prompt_ctx = PromptContext(
        input_summary=runtime.user_prompt,
        current_spec=plan.normalized_spec.model_dump(),
        assumptions=[{"topic": a.topic, "assumption": a.assumption} for a in plan.assumptions],
        research_findings=findings,
        prior_review=prior_review,
    )
    parts = [
        f"Design brief:\n{plan.design_brief}",
        f"Context (JSON):\n{prompt_ctx.to_prompt_text()}",
        (
            "Apply patches to model.py to implement the design. Test your changes using "
            "test_build_model. When successful, return CadSourceResult. The harness will "
            "do the final deterministic build, inspect, and render."
        ),
    ]
    if failure_feedback is not None:
        parts.append(
            "CAD_VALIDATION_FAILURE_FEEDBACK (JSON):\n" + failure_feedback.model_dump_json(indent=2)
        )
        parts.append(
            "Repair the source to address this exact failed command. Preserve "
            "spec intent unless the failure shows the implementation strategy is invalid."
        )
    return "\n\n".join(parts)


def _command_failure(
    *,
    revision_attempt: int,
    source_attempt: int,
    attempt_dir: Path,
    phase: str,
    command: str,
    timeout_s: float | None,
    elapsed_s: float,
    exc: BaseException,
) -> tuple[CadCommandEvidence, CadFailureFeedback]:
    returncode: int | None = None
    stdout = ""
    stderr = ""
    cmd_label = command
    detail = str(exc)
    if isinstance(exc, CliError):
        returncode = exc.returncode
        stdout = exc.stdout
        stderr = exc.stderr
        cmd_label = " ".join(exc.cmd) if exc.cmd else command
        if exc.cli_error_traceback:
            detail = f"{detail}\n\nTraceback (from cad-cli):\n{exc.cli_error_traceback}"
    evidence = CadCommandEvidence(
        command=cmd_label,
        status="failed",
        duration_s=round(elapsed_s, 3),
        timeout_s=timeout_s,
        returncode=returncode,
        summary=detail[:500],
        stdout_snippet=_clip(stdout),
        stderr_snippet=_clip(stderr),
        error_type=type(exc).__name__,
    )
    feedback = CadFailureFeedback(
        revision_attempt=revision_attempt,
        source_attempt=source_attempt,
        failed_phase=phase,
        failed_command=cmd_label,
        summary=f"{phase} failed: {detail[:500]}",
        detail=detail[:2000],
        returncode=returncode,
        stdout_snippet=_clip(stdout),
        stderr_snippet=_clip(stderr),
        timeout_s=timeout_s,
        elapsed_s=round(elapsed_s, 3),
        debug_artifact_path=str(attempt_dir),
        repair_instructions=[
            "Use ApplyPatchTool to apply a minimal fix to model.py.",
            "Use test_build_model to ensure your fix resolves the issue.",
            "Once successful, return CadSourceResult.",
            "Use the failed command stderr/stdout to make the smallest source fix.",
        ],
    )
    return evidence, feedback


def _artifact_failure(
    *,
    revision_attempt: int,
    source_attempt: int,
    attempt_dir: Path,
    phase: str,
    command: str,
    message: str,
    evidence: CadCommandEvidence,
) -> CadFailureFeedback:
    evidence.status = "failed"
    evidence.summary = message
    return CadFailureFeedback(
        revision_attempt=revision_attempt,
        source_attempt=source_attempt,
        failed_phase=phase,
        failed_command=command,
        summary=message,
        detail=message,
        debug_artifact_path=str(attempt_dir),
        repair_instructions=[
            "Use ApplyPatchTool to apply a fix to model.py.",
            "The command returned successfully but did not produce the required artifact bundle.",
        ],
    )


def _successful_command(
    *,
    command: str,
    duration_s: float,
    timeout_s: float | None,
    summary: str,
    output_dir: str | None = None,
    metadata_path: str | None = None,
) -> CadCommandEvidence:
    return CadCommandEvidence(
        command=command,
        status="ok",
        duration_s=round(duration_s, 3),
        timeout_s=timeout_s,
        returncode=0,
        summary=summary,
        output_dir=output_dir,
        metadata_path=metadata_path,
    )


def _write_validation_artifacts(
    attempt_dir: Path,
    *,
    source_result: CadSourceResult,
    validation: CadValidationResult,
) -> None:
    _write_json(attempt_dir / "source-result.json", source_result.model_dump())
    _write_json(attempt_dir / "validation-result.json", validation.model_dump())
    if validation.failure_feedback is not None:
        _write_json(
            attempt_dir / "failure-feedback.json",
            validation.failure_feedback.model_dump(),
        )


def _validate_cad_source(
    runtime: PhaseRuntimeContext,
    *,
    revision_attempt: int,
    source_attempt: int,
    source_result: CadSourceResult,
) -> CadValidationResult:
    attempt_ordinal, attempt_dir = _next_source_attempt_dir(runtime.run_root)
    model_path = runtime.run_ctx.source_dir / "model.py"
    
    debug_model_path = attempt_dir / "model.py"
    if model_path.exists():
        debug_model_path.parent.mkdir(parents=True, exist_ok=True)
        debug_model_path.write_text(model_path.read_text())
        
    logger.info(
        "cad source attempt: ordinal=%d revision_attempt=%d source_attempt=%d path=%s",
        attempt_ordinal,
        revision_attempt,
        source_attempt,
        attempt_dir,
    )
    validation = CadValidationResult(
        ok=False,
        revision_attempt=revision_attempt,
        source_attempt=source_attempt,
        debug_dir=str(attempt_dir),
        source_path=str(debug_model_path),
    )

    build_dir = attempt_dir / "build"
    start = time.monotonic()
    logger.info(
        "cad validation start: command=cad build revision_attempt=%d "
        "source_attempt=%d timeout=%ss dir=%s",
        revision_attempt,
        source_attempt,
        runtime.run_ctx.timeouts.cad_build,
        attempt_dir,
    )
    try:
        build: CadBuildResult = cad_build(
            model_path=model_path,
            output_dir=build_dir,
            timeout=runtime.run_ctx.timeouts.cad_build,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - start
        evidence, feedback = _command_failure(
            revision_attempt=revision_attempt,
            source_attempt=source_attempt,
            attempt_dir=attempt_dir,
            phase="build",
            command="cad build",
            timeout_s=runtime.run_ctx.timeouts.cad_build,
            elapsed_s=elapsed,
            exc=exc,
        )
        validation.commands.append(evidence)
        validation.failure_feedback = feedback
        _write_validation_artifacts(attempt_dir, source_result=source_result, validation=validation)
        return validation
    elapsed = time.monotonic() - start
    build_evidence = _successful_command(
        command="cad build",
        duration_s=elapsed,
        timeout_s=runtime.run_ctx.timeouts.cad_build,
        summary=build.summary,
        output_dir=build.output_dir,
        metadata_path=build.metadata_path,
    )
    validation.commands.append(build_evidence)
    validation.build_ok = True
    validation.build_result = build.model_dump()
    _write_json(attempt_dir / "build-result.json", build.model_dump())
    missing_build = [
        str(path)
        for path in (build.step_path, build.glb_path, Path(build.metadata_path))
        if not path.is_file()
    ]
    if missing_build:
        validation.failure_feedback = _artifact_failure(
            revision_attempt=revision_attempt,
            source_attempt=source_attempt,
            attempt_dir=attempt_dir,
            phase="build",
            command="cad build",
            message="cad build did not produce required artifacts: " + ", ".join(missing_build),
            evidence=build_evidence,
        )
        validation.build_ok = False
        _write_validation_artifacts(attempt_dir, source_result=source_result, validation=validation)
        return validation

    start = time.monotonic()
    logger.info(
        "cad validation start: command=cad inspect summary revision_attempt=%d "
        "source_attempt=%d timeout=%ss",
        revision_attempt,
        source_attempt,
        runtime.run_ctx.timeouts.cad_inspect,
    )
    try:
        inspect: CadInspectResult = cad_inspect_summary(
            build.step_path,
            timeout=runtime.run_ctx.timeouts.cad_inspect,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - start
        evidence, feedback = _command_failure(
            revision_attempt=revision_attempt,
            source_attempt=source_attempt,
            attempt_dir=attempt_dir,
            phase="inspect",
            command="cad inspect summary",
            timeout_s=runtime.run_ctx.timeouts.cad_inspect,
            elapsed_s=elapsed,
            exc=exc,
        )
        validation.commands.append(evidence)
        validation.failure_feedback = feedback
        _write_validation_artifacts(attempt_dir, source_result=source_result, validation=validation)
        return validation
    elapsed = time.monotonic() - start
    inspect_evidence = _successful_command(
        command="cad inspect summary",
        duration_s=elapsed,
        timeout_s=runtime.run_ctx.timeouts.cad_inspect,
        summary=inspect.summary,
    )
    validation.commands.append(inspect_evidence)
    validation.inspect_ok = True
    validation.inspect_result = inspect.model_dump()
    _write_json(attempt_dir / "inspect-summary.json", inspect.model_dump())

    render_dir = attempt_dir / "render"
    start = time.monotonic()
    logger.info(
        "cad validation start: command=cad render revision_attempt=%d "
        "source_attempt=%d timeout=%ss",
        revision_attempt,
        source_attempt,
        runtime.run_ctx.timeouts.cad_render,
    )
    try:
        render: CadRenderResult = cad_render(
            glb_path=build.glb_path,
            output_dir=render_dir,
            timeout=runtime.run_ctx.timeouts.cad_render,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - start
        evidence, feedback = _command_failure(
            revision_attempt=revision_attempt,
            source_attempt=source_attempt,
            attempt_dir=attempt_dir,
            phase="render",
            command="cad render",
            timeout_s=runtime.run_ctx.timeouts.cad_render,
            elapsed_s=elapsed,
            exc=exc,
        )
        validation.commands.append(evidence)
        validation.failure_feedback = feedback
        _write_validation_artifacts(attempt_dir, source_result=source_result, validation=validation)
        return validation
    elapsed = time.monotonic() - start
    render_evidence = _successful_command(
        command="cad render",
        duration_s=elapsed,
        timeout_s=runtime.run_ctx.timeouts.cad_render,
        summary=render.summary,
        output_dir=render.output_dir,
        metadata_path=render.metadata_path,
    )
    validation.commands.append(render_evidence)
    validation.render_ok = True
    validation.render_result = render.model_dump()
    _write_json(attempt_dir / "render-result.json", render.model_dump())
    missing_render = [
        str(path)
        for path in (render.sheet_path, Path(render.metadata_path), *render.view_paths())
        if not path.is_file()
    ]
    if missing_render:
        validation.failure_feedback = _artifact_failure(
            revision_attempt=revision_attempt,
            source_attempt=source_attempt,
            attempt_dir=attempt_dir,
            phase="render",
            command="cad render",
            message="cad render did not produce required artifacts: " + ", ".join(missing_render),
            evidence=render_evidence,
        )
        validation.render_ok = False
        _write_validation_artifacts(attempt_dir, source_result=source_result, validation=validation)
        return validation

    validation.ok = True
    _write_validation_artifacts(attempt_dir, source_result=source_result, validation=validation)
    runtime.run_ctx.notes["last_source_attempt_dir"] = str(attempt_dir)
    runtime.run_ctx.notes["last_build"] = build.model_dump()
    runtime.run_ctx.notes["last_inspect"] = inspect.model_dump()
    runtime.run_ctx.notes["last_render"] = render.model_dump()
    logger.info(
        "cad validation completed: revision_attempt=%d source_attempt=%d debug_dir=%s",
        revision_attempt,
        source_attempt,
        attempt_dir,
    )
    return validation


def _cad_revision_from_validation(
    source_result: CadSourceResult, validation: CadValidationResult
) -> CadRevisionResult:
    return CadRevisionResult(
        build_ok=validation.build_ok,
        inspect_ok=validation.inspect_ok,
        render_ok=validation.render_ok,
        revision_notes=source_result.revision_notes,
        known_risks=list(source_result.known_risks),
        dimensions=dict(source_result.self_reported_dimensions),
        build_errors=[]
        if validation.ok
        else [validation.failure_feedback.summary]
        if validation.failure_feedback
        else ["CAD validation failed"],
    )


async def _author_and_validate_source(
    ctx: OrchestrationPhaseContext,
    runtime: PhaseRuntimeContext,
    *,
    plan,
    findings: list[dict],
    prior_review: dict | None,
    revision_attempt: int,
) -> tuple[CadSourceResult | None, CadValidationResult]:
    failure_feedback: CadFailureFeedback | None = None
    last_source_result: CadSourceResult | None = None
    last_validation: CadValidationResult | None = None

    for source_attempt in range(1, MAX_SOURCE_ATTEMPTS + 1):
        designer_input = _format_designer_input(
            plan=plan,
            runtime=runtime,
            findings=findings,
            prior_review=prior_review,
            failure_feedback=failure_feedback,
        )
        source_result = await ctx.design_revision(designer_input, runtime.run_ctx, runtime.profile)
        last_source_result = source_result
        ctx.emit(
            runtime.run.run_name,
            ProgressEventKind.cad_source_authored,
            message=f"CAD source authored ({source_attempt}/{MAX_SOURCE_ATTEMPTS})",
            data={
                "revision_attempt": revision_attempt,
                "source_attempt": source_attempt,
                "known_risks": list(source_result.known_risks)[:3],
            },
        )
        ctx.emit(
            runtime.run.run_name,
            ProgressEventKind.cad_validation_started,
            message=f"validating CAD source ({source_attempt}/{MAX_SOURCE_ATTEMPTS})",
            data={
                "revision_attempt": revision_attempt,
                "source_attempt": source_attempt,
                "commands": ["cad build", "cad inspect summary", "cad render"],
            },
        )
        validation = _validate_cad_source(
            runtime,
            revision_attempt=revision_attempt,
            source_attempt=source_attempt,
            source_result=source_result,
        )
        last_validation = validation
        if validation.ok:
            ctx.emit(
                runtime.run.run_name,
                ProgressEventKind.cad_validation_completed,
                message="CAD validation completed",
                data={
                    "revision_attempt": revision_attempt,
                    "source_attempt": source_attempt,
                    "debug_artifact_path": validation.debug_dir,
                    "command_count": len(validation.commands),
                },
            )
            return source_result, validation

        failure_feedback = validation.failure_feedback
        ctx.emit(
            runtime.run.run_name,
            ProgressEventKind.cad_validation_failed,
            message=failure_feedback.summary if failure_feedback else "CAD validation failed",
            data={
                "revision_attempt": revision_attempt,
                "source_attempt": source_attempt,
                "debug_artifact_path": validation.debug_dir,
                "failed_phase": failure_feedback.failed_phase if failure_feedback else None,
                "failed_command": failure_feedback.failed_command if failure_feedback else None,
                "returncode": failure_feedback.returncode if failure_feedback else None,
            },
        )
        logger.warning(
            "cad validation failed: revision_attempt=%d source_attempt=%d "
            "phase=%s command=%s dir=%s",
            revision_attempt,
            source_attempt,
            failure_feedback.failed_phase if failure_feedback else "?",
            failure_feedback.failed_command if failure_feedback else "?",
            validation.debug_dir,
        )

    assert last_validation is not None
    return last_source_result, last_validation


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
        logger.info("revision attempt: %d/%d", attempt, max_revisions)
        runtime.run_ctx.notes["revision_attempt"] = attempt
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

        source_result, validation = await _author_and_validate_source(
            ctx,
            runtime,
            plan=plan,
            findings=findings,
            prior_review=prior_review,
            revision_attempt=attempt,
        )
        assert source_result is not None
        cad_out = _cad_revision_from_validation(source_result, validation)
        logger.info(
            "revision validation result: attempt=%d build=%s render=%s inspect=%s",
            attempt,
            cad_out.build_ok,
            cad_out.render_ok,
            cad_out.inspect_ok,
        )
        ctx.emit(
            run.run_name,
            ProgressEventKind.revision_built,
            message=f"harness validation build_ok={cad_out.build_ok} render_ok={cad_out.render_ok}",
            data={
                "build_ok": cad_out.build_ok,
                "inspect_ok": cad_out.inspect_ok,
                "render_ok": cad_out.render_ok,
                "dimensions": cad_out.dimensions,
                "debug_artifact_path": validation.debug_dir,
            },
        )
        await ctx.narrate(
            run.run_name,
            phase="revision",
            just_completed="finished deterministic CAD validation",
            next_step="send it to review" if validation.ok else "stop with diagnosable failure",
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

        if not validation.ok:
            ctx.emit(
                run.run_name,
                ProgressEventKind.breadcrumb,
                message="CAD validation exhausted debug loops; not persisting",
                data={
                    "attempt": attempt,
                    "debug_artifact_path": validation.debug_dir,
                    "build_errors": cad_out.build_errors[:3],
                },
            )
            break

        build_dir = Path(runtime.run_ctx.notes["last_build"]["output_dir"])
        render_dir = Path(runtime.run_ctx.notes["last_render"]["output_dir"])
        staging = _staging_views_dir(runtime.run_root, attempt)
        staged_views = _stage_views(render_dir, staging)

        build_meta = Path(runtime.run_ctx.notes["last_build"]["metadata_path"])
        render_meta = Path(runtime.run_ctx.notes["last_render"]["metadata_path"])
        inspect_src = Path(validation.debug_dir) / "inspect-summary.json"

        if (
            not staged_views
            or not inspect_src.is_file()
            or not build_meta.is_file()
            or not render_meta.is_file()
        ):
            ctx.emit(
                run.run_name,
                ProgressEventKind.cad_validation_failed,
                message="complete revision bundle check failed after validation",
                data={
                    "attempt": attempt,
                    "debug_artifact_path": validation.debug_dir,
                    "staged_views": len(staged_views),
                    "has_inspect": inspect_src.is_file(),
                    "has_build_metadata": build_meta.is_file(),
                    "has_render_metadata": render_meta.is_file(),
                },
            )
            break

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
            build_metadata_src=build_meta,
            render_metadata_src=render_meta,
            inspect_summary_src=inspect_src,
        )
        fresh = ctx.load_run(run.run_name)
        revision, _ = ctx.persist_revision(fresh, bundle)
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
            delivered = revision.revision_name
            ctx.emit(run.run_name, ProgressEventKind.breadcrumb, message="revision accepted")
            break
        prior_review = review.model_dump()

    return delivered
