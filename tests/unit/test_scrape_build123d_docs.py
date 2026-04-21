"""Unit tests: the Build123D doc scraper's pure-function pieces.

REQ: FLH-F-029, FLH-D-026

The scraper itself is build-time tooling (``scripts/scrape_build123d_docs.py``)
— we exercise the HTML-to-markdown pipeline and the overlay-merging logic
against local fixtures so network isn't required. Skips when the optional
``scrape`` dependency group isn't installed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Skip the whole file if markdownify/bs4 aren't available (CI or a minimal env).
pytest.importorskip("bs4")
pytest.importorskip("markdownify")

SCRAPER_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "scrape_build123d_docs.py"
)


def _load_scraper():
    name = "_scraper_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRAPER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Must register before exec so @dataclass annotation resolution works.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_HTML = """<!doctype html>
<html><body>
<div class="wy-nav-content">
  <div role="main">
    <div itemprop="articleBody">
      <h1>Sample Page<a class="headerlink" href="#sample-page">¶</a></h1>
      <p>Intro paragraph with a <a href="#anchor">relative link</a>.</p>
      <div class="highlight-python notranslate">
        <div class="highlight"><pre>from build123d import Box
b = Box(10, 20, 30)
</pre></div>
      </div>
      <h2>Objects</h2>
      <ul>
        <li><a href="objects.html#foo"><code>Box</code></a> — a box.</li>
        <li><a href="objects.html#cyl"><code>Cylinder</code></a> — a cylinder.</li>
      </ul>
    </div>
  </div>
</div>
</body></html>
"""


def test_extract_main_strips_noise_and_resolves_links() -> None:
    scraper = _load_scraper()
    main = scraper._extract_main(SAMPLE_HTML, "https://example.test/page.html")
    # headerlink ¶ stripped
    assert main.find("a", class_="headerlink") is None
    # relative href resolved
    anchor_a = [a for a in main.find_all("a", href=True) if a.get_text(strip=True) == "relative link"]
    assert anchor_a
    assert anchor_a[0]["href"].startswith("https://example.test/")


def test_to_markdown_preserves_code_fence() -> None:
    scraper = _load_scraper()
    main = scraper._extract_main(SAMPLE_HTML, "https://example.test/page.html")
    md = scraper._to_markdown(main)
    # Fenced python block must survive
    assert "```python" in md
    assert "Box(10, 20, 30)" in md


def test_apply_overlay_attaches_to_canonical_catalog_link() -> None:
    scraper = _load_scraper()
    objects_md = (
        "# Objects\n\n"
        "[`Box`](https://example.test/objects.html#box)\n\n"
        "Box defined by length, width, height.\n\n"
        "[`Cylinder`](https://example.test/objects.html#cyl)\n\n"
    )
    overlay = (
        "# Overlay\n\n"
        "## MARKER: Box\n"
        "*(via bd_test_lib)*\n\n"
        "## MARKER: Cylinder\n"
        "*(thread variants via bd_warehouse)*\n\n"
    )
    merged = scraper._apply_overlay(objects_md, overlay)
    lines = merged.splitlines()
    # The annotation appears on the same line as the canonical link entry
    assert any(
        "[`Box`]" in ln and "via bd_test_lib" in ln for ln in lines
    ), merged
    assert any(
        "[`Cylinder`]" in ln and "via bd_warehouse" in ln for ln in lines
    ), merged


def test_apply_overlay_falls_back_to_external_extensions_section() -> None:
    scraper = _load_scraper()
    objects_md = "# Objects\n\nNo matching entries here.\n"
    overlay = (
        "## MARKER: Extrude\n*(v-slot via bd_vslot)*\n"
    )
    merged = scraper._apply_overlay(objects_md, overlay)
    assert "## External library extensions" in merged
    assert "v-slot via bd_vslot" in merged
    assert "**Extrude**" in merged


def test_apply_overlay_never_attaches_twice() -> None:
    # If a slug appears in multiple forms the annotation should still attach
    # once at the canonical catalog link, not duplicated.
    scraper = _load_scraper()
    objects_md = (
        "[`Sphere`](https://example.test/#sphere)\n\n"
        "Sphere defined by radius.\n\n"
        "*class* Sphere(*radius: float*)\n"
    )
    overlay = "## MARKER: Sphere\n*(bearings via bd_warehouse)*\n"
    merged = scraper._apply_overlay(objects_md, overlay)
    assert merged.count("bearings via bd_warehouse") == 1
