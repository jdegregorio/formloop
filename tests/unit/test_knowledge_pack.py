"""Unit tests: Build123D knowledge pack loader and search.

REQ: FLH-F-029, FLH-D-026
"""

from __future__ import annotations

import json
from importlib.resources import files

import pytest

from formloop.agents import knowledge


EXPECTED_SLUGS = [
    "key_concepts",
    "key_concepts_builder",
    "key_concepts_algebra",
    "moving_objects",
    "objects",
    "operations",
    "topology_selection",
    "builders",
    "joints",
    "assemblies",
    "import_export",
    "cheat_sheet",
]


def test_all_twelve_slugs_present() -> None:
    slugs = knowledge.list_slugs()
    assert slugs == EXPECTED_SLUGS, slugs


def test_index_entries_have_upstream_urls() -> None:
    index = knowledge.load_index()
    for entry in index["pages"]:
        assert entry["source_url"].startswith("https://build123d.readthedocs.io/")
        assert entry["source_url"].endswith(".html")
        assert entry["char_count"] > 100  # pages are never stubs


def test_load_page_round_trips_cheat_sheet() -> None:
    md = knowledge.load_page("cheat_sheet")
    assert "# Cheat Sheet" in md
    # The page header the scraper emits includes a link to the upstream URL.
    assert "build123d.readthedocs.io/en/latest/cheat_sheet.html" in md


def test_load_page_raises_on_unknown_slug() -> None:
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.load_page("no_such_page")


def test_page_metadata_raises_on_unknown_slug() -> None:
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.page_metadata("no_such_page")


def test_search_topic_topology_selection_returns_right_page() -> None:
    # Heading-level match — the slug itself contains both tokens.
    out = knowledge.search_topic("topology selection", max_chars=1500)
    assert "topology_selection" in out
    assert "Topology Selection" in out


def test_search_topic_external_lib_resolves_through_overlay() -> None:
    # The overlay annotations live in objects.md body text, not in headings.
    # A distinctive query like the lib name itself must land on a page that
    # cites it — proving the agent can discover the external libs through
    # the lookup tool.
    out = knowledge.search_topic("bd_warehouse threaded", max_chars=2000)
    assert "bd_warehouse" in out, out[:500]


def test_search_topic_unknown_keyword_returns_fallback_with_slugs() -> None:
    out = knowledge.search_topic("asdf_definitely_not_in_docs_xyz")
    assert "No match" in out
    # Fallback should list the available slugs so the agent can pivot
    for slug in ("cheat_sheet", "objects", "operations"):
        assert slug in out


def test_search_topic_empty_returns_fallback() -> None:
    out = knowledge.search_topic("")
    assert "No topic" in out or "No match" in out


def test_search_topic_respects_max_chars() -> None:
    out = knowledge.search_topic("objects", max_chars=500)
    assert len(out) <= 500 + 400  # header + truncation marker overhead


def test_cheat_sheet_excerpt_is_bounded() -> None:
    out = knowledge.cheat_sheet_excerpt(max_chars=4000)
    assert 0 < len(out) <= 4000 + 200
    assert "# Cheat Sheet" in out


def test_external_libs_overlay_file_is_shipped() -> None:
    # The curated overlay lives inside the installed package so it can be
    # audited/reviewed alongside the scraped output.
    resource = files("formloop.agents.knowledge.build123d").joinpath(
        "external_libs_overlay.md"
    )
    # iterdir is stable across extracted and frozen wheels
    body = resource.read_text(encoding="utf-8")
    for lib in ("bd_warehouse", "bd_vslot", "py_gearworks", "bd_beams_and_bars"):
        assert lib in body


def test_last_scraped_stamp_present() -> None:
    resource = files("formloop.agents.knowledge.build123d").joinpath("last-scraped.json")
    stamp = json.loads(resource.read_text(encoding="utf-8"))
    assert "scraped_at" in stamp
    assert stamp["page_count"] == len(EXPECTED_SLUGS)
