"""Narration sanitization and fallback helpers.

REQ: FLH-F-024, FLH-F-026, FLH-D-013, FLH-D-025, FLH-NF-010
"""

from __future__ import annotations

import re as _re
from typing import Any

from ..agents.cad_designer import CadRevisionResult
from ..agents.manager import ManagerPlan

_FORBIDDEN_PATTERNS = (
    _re.compile(r"run-\d+"),
    _re.compile(r"rev-\d+"),
    _re.compile(r"[/\\][\w./\\-]+\.(?:step|glb|png|json|py)"),
    _re.compile(r"/var/[\w./\\-]+"),
)


def _scrub(text: str) -> str:
    for pat in _FORBIDDEN_PATTERNS:
        text = pat.sub("", text)
    return text.strip()


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _scrub(value)
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    return value


def sanitize_context(ctx: dict[str, Any]) -> dict[str, Any]:
    return {k: sanitize_value(v) for k, v in ctx.items()}


def fallback_plan(plan: ManagerPlan) -> str:
    bits = []
    if plan.assumptions:
        first = plan.assumptions[0]
        bits.append(f"resolved {len(plan.assumptions)} ambiguities (e.g. {first.topic})")
    if plan.research_topics:
        bits.append(f"lined up {len(plan.research_topics)} research topic(s)")
    return "we normalized the spec: " + "; ".join(bits) if bits else "we normalized the spec"


def fallback_research(findings: list[dict], failures: int) -> str:
    if not findings:
        return "research complete"
    topics = ", ".join(f.get("topic", "") for f in findings[:2] if f.get("topic"))
    tail = f" ({failures} failed)" if failures else ""
    return f"research on {topics}{tail}" if topics else f"research complete{tail}"


def fallback_revision_built(cad_out: CadRevisionResult) -> str:
    if not (cad_out.build_ok and cad_out.render_ok):
        return "build or render did not complete cleanly; we'll retry"
    dims = cad_out.dimensions or {}
    size_bits = []
    for key in ("overall", "size", "width", "length", "height"):
        if key in dims:
            size_bits.append(f"{key}={dims[key]}")
            if len(size_bits) >= 2:
                break
    if size_bits:
        return "designer landed on " + ", ".join(size_bits)
    return "designer produced a clean build"


def fallback_review(review) -> str:
    decision = review.decision.value if review.decision else "reviewed"
    if review.key_findings:
        return f"review {decision}: {review.key_findings[0][:160]}"
    return f"review {decision}"
