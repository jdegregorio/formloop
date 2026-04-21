"""Knowledge pack loader for the CAD Designer.

The Build123D docs are scraped (via ``scripts/scrape_build123d_docs.py``) and
committed as markdown under ``build123d/pages/``. This module is the runtime
reader — it loads individual pages via :mod:`importlib.resources` so the pack
works equally well from an editable checkout and from an installed wheel.

REQ: FLH-F-029, FLH-D-026
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import as_file, files
from typing import Any

_PKG = "formloop.agents.knowledge.build123d"
_PAGES_PKG = f"{_PKG}.pages"


class KnowledgeError(LookupError):
    """Raised when a requested knowledge asset isn't available."""


@lru_cache(maxsize=1)
def load_index() -> dict[str, Any]:
    """Return the knowledge-pack manifest (``index.json``).

    Shape::

        {
          "pages": [
            {"slug": "cheat_sheet", "title": "Cheat Sheet",
             "source_url": "https://build123d.readthedocs.io/.../cheat_sheet.html",
             "headings": [...], "char_count": 24884},
            ...
          ]
        }
    """
    try:
        resource = files(_PKG).joinpath("index.json")
    except ModuleNotFoundError as exc:
        raise KnowledgeError(
            "Build123D knowledge pack is not installed. Run "
            "`uv run --extra scrape python scripts/scrape_build123d_docs.py`."
        ) from exc
    with as_file(resource) as path:
        return json.loads(path.read_text(encoding="utf-8"))


def list_slugs() -> list[str]:
    """Return the ordered list of slugs present in the knowledge pack."""
    return [entry["slug"] for entry in load_index()["pages"]]


def page_metadata(slug: str) -> dict[str, Any]:
    """Return the index entry for ``slug``, or raise :class:`KnowledgeError`."""
    for entry in load_index()["pages"]:
        if entry["slug"] == slug:
            return entry
    raise KnowledgeError(
        f"no such knowledge page: {slug!r}. Available: {list_slugs()!r}"
    )


def load_page(slug: str) -> str:
    """Return the full markdown body of the ``slug`` page.

    Raises :class:`KnowledgeError` for unknown slugs.
    """
    page_metadata(slug)  # validates slug
    try:
        resource = files(_PAGES_PKG).joinpath(f"{slug}.md")
    except ModuleNotFoundError as exc:  # pragma: no cover — pack missing
        raise KnowledgeError(f"pages subpackage missing: {exc}") from exc
    with as_file(resource) as path:
        if not path.exists():
            raise KnowledgeError(f"page file missing on disk: {slug}")
        return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Topic search
# ---------------------------------------------------------------------------


def _score_entry_head(entry: dict[str, Any], tokens: list[str]) -> int:
    """Heading-level score: slug + title + H1/H2/H3 text."""
    haystack = " ".join(
        [entry["slug"], entry.get("title", ""), " ".join(entry.get("headings", []))]
    ).lower()
    return sum(haystack.count(t) for t in tokens)


def _score_entry_body(slug: str, tokens: list[str]) -> int:
    """Body-level score: count token occurrences in the full page body."""
    try:
        body = load_page(slug).lower()
    except KnowledgeError:
        return 0
    return sum(body.count(t) for t in tokens)


def search_topic(topic: str, *, max_chars: int = 1500) -> str:
    """Return a short excerpt from the best-matching page for ``topic``.

    Keyword-matching is intentionally simple: tokenize the query, score each
    page first by slug/title/heading overlap (cheap), and — if that score is
    zero — fall back to a body scan so keywords that appear only in prose or
    in the external-lib overlay (e.g. ``threaded rod``) still resolve. Returns
    either the relevant heading subsection or the head of the page, truncated
    to ``max_chars``. Exact slug matches always win.
    """
    norm = topic.strip()
    if not norm:
        return _no_match_fallback()

    tokens = [t for t in re.findall(r"[a-zA-Z0-9_]+", norm.lower()) if len(t) >= 2]
    if not tokens:
        return _no_match_fallback()

    entries = load_index()["pages"]

    # Direct slug hit wins
    for e in entries:
        if e["slug"] == norm:
            return _format_match(e, load_page(e["slug"]).strip(), max_chars)

    # Heading/title score
    ranked = sorted(entries, key=lambda e: _score_entry_head(e, tokens), reverse=True)
    best = ranked[0]
    if _score_entry_head(best, tokens) == 0:
        # Body-level fallback
        ranked = sorted(entries, key=lambda e: _score_entry_body(e["slug"], tokens), reverse=True)
        best = ranked[0]
        if _score_entry_body(best["slug"], tokens) == 0:
            return _no_match_fallback(query=topic)

    page = load_page(best["slug"])
    excerpt = _extract_section(page, tokens) or _extract_body_context(page, tokens) or page
    return _format_match(best, excerpt.strip(), max_chars)


def _format_match(entry: dict[str, Any], excerpt: str, max_chars: int) -> str:
    if len(excerpt) > max_chars:
        excerpt = (
            excerpt[:max_chars].rstrip()
            + f"\n\n…(truncated; full page: `build123d_lookup('{entry['slug']}')` "
            f"or see {entry['source_url']})"
        )
    return (
        f"# Match: `{entry['slug']}` — {entry.get('title', entry['slug'])}\n"
        f"Source: {entry['source_url']}\n\n{excerpt}"
    )


def _extract_body_context(md: str, tokens: list[str], *, window: int = 800) -> str | None:
    """Return a ~window-char slice centered on the first token occurrence."""
    body = md.lower()
    for t in tokens:
        idx = body.find(t)
        if idx >= 0:
            start = max(0, idx - window // 2)
            end = min(len(md), idx + window // 2)
            # Align to line boundaries when possible
            start = md.rfind("\n", 0, start) + 1
            nl = md.find("\n", end)
            if nl >= 0:
                end = nl
            return md[start:end]
    return None


def _extract_section(md: str, tokens: list[str]) -> str | None:
    """Return the first H2/H3 section whose heading contains any token."""
    # Split on markdown headings, keep the heading with its body
    parts = re.split(r"(?m)^(#{1,3} .+)$", md)
    # parts is interleaved: [preamble, heading1, body1, heading2, body2, ...]
    if len(parts) < 3:
        return None
    for i in range(1, len(parts), 2):
        heading = parts[i].lower()
        if any(t in heading for t in tokens):
            body = parts[i + 1] if i + 1 < len(parts) else ""
            return parts[i] + body
    return None


def _no_match_fallback(*, query: str | None = None) -> str:
    slugs = list_slugs()
    prefix = (
        f"# No match for {query!r}\n\n" if query else "# No topic provided\n\n"
    )
    lines = [prefix, "Available knowledge pack slugs:"]
    for s in slugs:
        lines.append(f"- `{s}`")
    lines.append(
        "\nCall `build123d_lookup(slug)` with a slug above, or with a keyword "
        "like `threaded rod`, `topology selection`, `mirror`."
    )
    return "\n".join(lines)


def cheat_sheet_excerpt(max_chars: int = 12000) -> str:
    """Return a trimmed cheat-sheet slice suitable for static INSTRUCTIONS.

    The full cheat_sheet.md is verbose (~25k chars); we slice the head to keep
    token cost bounded. If the pack isn't present yet (e.g. CI build before the
    scraper has been run), return an empty string — the INSTRUCTIONS scaffold
    degrades gracefully.
    """
    try:
        page = load_page("cheat_sheet")
    except KnowledgeError:
        return ""
    if len(page) <= max_chars:
        return page
    return page[:max_chars].rstrip() + "\n\n…(truncated; call build123d_lookup('cheat_sheet') for full page)"
