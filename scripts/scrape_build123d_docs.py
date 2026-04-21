"""Scrape the official Build123D documentation into a local knowledge pack.

This is a **build-time tool**, not a harness runtime dep — its dependencies live
in the ``scrape`` optional-dep group. Run it with:

    uv run --extra scrape python scripts/scrape_build123d_docs.py

The output is committed under ``src/formloop/agents/knowledge/build123d/`` so
runs are reproducible, reviewable in PRs, and don't require network access at
serving time. The CAD Designer loads pages through :mod:`formloop.agents.knowledge`.

REQ: FLH-F-029, FLH-D-026
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from markdownify import MarkdownConverter  # noqa: F401 — imported for future use


def _normalize_code_blocks(soup: BeautifulSoup) -> None:
    """Pre-process Sphinx highlight blocks so markdownify emits fenced code.

    Sphinx wraps code in ``<div class="highlight-python"><pre>...</pre></div>``.
    We lift the ``<pre>`` out and mark the language via a ``data-lang`` attr
    that the converter below recognizes by wrapping in a plain ``<code>`` tag.
    """
    for div in soup.select('div[class*="highlight-"]'):
        classes = div.get("class", [])
        lang = ""
        for c in classes:
            m = re.match(r"highlight-(\w+)", c)
            if m:
                lang = m.group(1)
                break
        pre = div.find("pre")
        if pre is None:
            continue
        text = pre.get_text()
        fenced = soup.new_tag("pre")
        fenced.string = f"```{lang}\n{text.rstrip()}\n```"
        div.replace_with(fenced)


BASE_URL = "https://build123d.readthedocs.io/en/latest/"

# Pages to scrape. Keep order stable so that index.json is deterministic.
PAGES: list[tuple[str, str]] = [
    ("key_concepts", "key_concepts.html"),
    ("key_concepts_builder", "key_concepts_builder.html"),
    ("key_concepts_algebra", "key_concepts_algebra.html"),
    ("moving_objects", "moving_objects.html"),
    ("objects", "objects.html"),
    ("operations", "operations.html"),
    ("topology_selection", "topology_selection.html"),
    ("builders", "builders.html"),
    ("joints", "joints.html"),
    ("assemblies", "assemblies.html"),
    ("import_export", "import_export.html"),
    ("cheat_sheet", "cheat_sheet.html"),
]

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "src" / "formloop" / "agents" / "knowledge" / "build123d"
PAGES_DIR = OUT_DIR / "pages"
OVERLAY_PATH = OUT_DIR / "external_libs_overlay.md"
INDEX_PATH = OUT_DIR / "index.json"
STAMP_PATH = OUT_DIR / "last-scraped.json"


@dataclass(frozen=True)
class PageRecord:
    slug: str
    title: str
    source_url: str
    headings: tuple[str, ...]
    char_count: int


def _fetch(url: str, client: httpx.Client) -> str:
    resp = client.get(url, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def _extract_main(html: str, base_url: str) -> Tag:
    """Return the main article body, with anchors resolved to absolute URLs."""
    soup = BeautifulSoup(html, "html.parser")
    _normalize_code_blocks(soup)
    main = soup.select_one('div[itemprop="articleBody"]')
    if main is None:
        # Fallback for future layout changes
        main = soup.select_one('div[role="main"]') or soup.select_one("article")
    if main is None:
        raise RuntimeError(f"could not locate main content in {base_url}")

    # Strip noise: permalink anchors ("¶"), edit-on-github ribbons, version banners
    for node in main.select('a.headerlink, .viewcode-link, .edit-this-page, '
                            '.rst-footer-buttons, .rst-breadcrumbs, .sphinxsidebar'):
        node.decompose()

    # Resolve relative hrefs to absolute so the agent can cite upstream
    for a in main.find_all("a", href=True):
        a["href"] = urljoin(base_url, a["href"])
    for img in main.find_all("img", src=True):
        img["src"] = urljoin(base_url, img["src"])

    return main


def _to_markdown(main: Tag) -> str:
    from markdownify import markdownify as md_convert

    md = md_convert(
        str(main),
        heading_style="ATX",
        bullets="-",
        code_language="python",
        strip=["script", "style"],
    )
    # Collapse 3+ blank lines to 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Trim trailing whitespace per line
    md = "\n".join(line.rstrip() for line in md.splitlines())
    # The pre-processor emits literal ``` fences inside a <pre> — markdownify
    # will wrap those in another code fence. Flatten that double-wrapping.
    md = re.sub(r"```\n```(\w*)\n", r"```\1\n", md)
    md = re.sub(r"\n```\n```\n", "\n```\n", md)
    return md.strip() + "\n"


def _extract_headings(main: Tag) -> tuple[str, ...]:
    heads: list[str] = []
    for h in main.find_all(["h1", "h2", "h3"]):
        txt = h.get_text(" ", strip=True)
        if txt and txt not in heads:
            heads.append(txt)
    return tuple(heads)


def _apply_overlay(objects_md: str, overlay_md: str) -> str:
    """Merge the external-lib overlay into objects.md.

    The overlay file is structured as a sequence of ``## MARKER: <slug>`` blocks
    followed by the annotation text to weave in. We try three patterns in
    preference order:

    1. A standalone Sphinx cross-reference link: a line that is only
       ``[`Slug`](https://...)`` plus optional trailing whitespace. This is the
       canonical entry in the catalog listing.
    2. A class-definition signature line: ``*class* Slug(...)``.
    3. (Fallback) Any line containing the slug as a whole word.

    Annotations that can't be attached are collected into an "External library
    extensions" subsection at the end of the page so the content is never
    silently dropped. We also never attach more than one annotation per slug.
    """
    blocks = re.split(r"^## MARKER: (\S+)\s*$", overlay_md, flags=re.MULTILINE)
    if len(blocks) < 3:
        return objects_md
    merged = objects_md
    unattached: list[tuple[str, str]] = []
    it = iter(blocks[1:])
    for slug, body in zip(it, it):
        ann = body.strip()
        if not ann:
            continue

        # Pattern 1: canonical catalog link line like `[`Slug`](url)`
        p1 = re.compile(
            rf"^(\[`{re.escape(slug)}`\]\([^)]+\)[^\n]*)$",
            re.MULTILINE,
        )
        m = p1.search(merged)
        if not m:
            # Pattern 2: class definition signature
            p2 = re.compile(
                rf"^(\*class\* {re.escape(slug)}\([^\n]*\*\))$",
                re.MULTILINE,
            )
            m = p2.search(merged)
        if not m:
            # Pattern 3: fallback — any whole-word occurrence, case-sensitive
            # (avoids matching 'box' inside 'text box' when slug is 'Box')
            p3 = re.compile(
                rf"^([^\n]*\b{re.escape(slug)}\b[^\n]*)$",
                re.MULTILINE,
            )
            for candidate in p3.finditer(merged):
                line = candidate.group(1)
                if "via bd_" in line or "via py_gearworks" in line:
                    continue
                m = candidate
                break

        if m and "via bd_" not in m.group(1) and "via py_gearworks" not in m.group(1):
            merged = merged[: m.start(1)] + m.group(1) + f"  {ann}" + merged[m.end(1) :]
        else:
            unattached.append((slug, ann))

    if unattached:
        extra = ["", "", "## External library extensions", ""]
        extra.append(
            "These capabilities are not part of the stock build123d `objects` "
            "module but are importable alongside it when the harness is "
            "installed. Use them only when the task genuinely calls for them; "
            "prefer stock primitives otherwise."
        )
        extra.append("")
        for slug, ann in unattached:
            extra.append(f"- **{slug}** — {ann}")
        merged = merged.rstrip() + "\n" + "\n".join(extra) + "\n"
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch and process in memory but do not write files")
    args = parser.parse_args()

    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    records: list[PageRecord] = []
    etags: dict[str, str | None] = {}

    headers = {
        "User-Agent": "formloop-build123d-scraper/1.0 "
                       "(https://github.com/jdegregorio/formloop)",
    }
    with httpx.Client(headers=headers) as client:
        for slug, path in PAGES:
            url = urljoin(BASE_URL, path)
            print(f"[scrape] {slug:22s} <- {url}", file=sys.stderr)
            html = _fetch(url, client)
            main = _extract_main(html, url)
            headings = _extract_headings(main)
            title = headings[0] if headings else slug.replace("_", " ").title()
            md = _to_markdown(main)
            # Front-matter-ish header so the agent can orient instantly
            header = (
                f"# {title}\n\n"
                f"_Source: [{url}]({url})_\n\n"
                f"_Part of the Build123D knowledge pack "
                f"(formloop/src/formloop/agents/knowledge/build123d/pages/{slug}.md)._\n\n"
                "---\n\n"
            )
            body = header + md
            if not args.dry_run:
                (PAGES_DIR / f"{slug}.md").write_text(body, encoding="utf-8")
            records.append(
                PageRecord(
                    slug=slug,
                    title=title,
                    source_url=url,
                    headings=headings,
                    char_count=len(body),
                )
            )
            etags[slug] = None  # could capture response.headers.get("etag")

    # Merge the curated overlay into objects.md so external-lib pointers appear
    # inline in the object catalog rather than as a separate section.
    if OVERLAY_PATH.exists() and not args.dry_run:
        objects_path = PAGES_DIR / "objects.md"
        if objects_path.exists():
            overlay_text = OVERLAY_PATH.read_text(encoding="utf-8")
            objects_md = objects_path.read_text(encoding="utf-8")
            merged = _apply_overlay(objects_md, overlay_text)
            objects_path.write_text(merged, encoding="utf-8")
            # Update char_count for the record so index.json stays accurate
            for i, rec in enumerate(records):
                if rec.slug == "objects":
                    records[i] = PageRecord(
                        slug=rec.slug,
                        title=rec.title,
                        source_url=rec.source_url,
                        headings=rec.headings,
                        char_count=len(merged),
                    )

    if not args.dry_run:
        INDEX_PATH.write_text(
            json.dumps(
                {
                    "pages": [
                        {
                            "slug": r.slug,
                            "title": r.title,
                            "source_url": r.source_url,
                            "headings": list(r.headings),
                            "char_count": r.char_count,
                        }
                        for r in records
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        STAMP_PATH.write_text(
            json.dumps(
                {
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "base_url": BASE_URL,
                    "page_count": len(records),
                    "etags": etags,
                    "scraper_version": 1,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    total = sum(r.char_count for r in records)
    print(f"[scrape] wrote {len(records)} pages, {total:,} chars total", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
