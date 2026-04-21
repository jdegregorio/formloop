"""The reviewer must actually receive the render sheet as an image.

REQ: FLH-F-006, FLH-F-007 — the Quality Specialist's primary artifact is the
7-view render sheet. Earlier revisions passed a text placeholder ("7-view
composite...") in the JSON payload and never handed the model a pixel, so
threaded rods without visible threads were sailing through review. These
tests pin down the fix: when a render sheet exists on disk, the reviewer
input is a multimodal message list with an ``input_image`` data URL; when no
images are available, it falls back to a plain string.
"""

from __future__ import annotations

import base64
from pathlib import Path

from formloop.orchestrator.run_driver import _build_reviewer_input, _png_to_data_url


# A minimal but valid PNG magic header + some bytes. The reviewer code only
# cares that the file exists and base64-encodes cleanly; it does not decode.
_PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def _write_png(path: Path, payload: bytes = b"pixels") -> Path:
    path.write_bytes(_PNG_HEADER + payload)
    return path


def test_png_to_data_url_returns_base64_data_uri(tmp_path: Path) -> None:
    path = _write_png(tmp_path / "sheet.png", b"ABCDE")
    url = _png_to_data_url(path)
    assert url is not None
    assert url.startswith("data:image/png;base64,")
    # Decoding the payload half should give back the bytes we wrote.
    prefix, b64 = url.split(",", 1)
    decoded = base64.b64decode(b64)
    assert decoded == _PNG_HEADER + b"ABCDE"


def test_png_to_data_url_none_when_missing(tmp_path: Path) -> None:
    assert _png_to_data_url(tmp_path / "missing.png") is None


def test_png_to_data_url_none_when_empty(tmp_path: Path) -> None:
    path = tmp_path / "empty.png"
    path.write_bytes(b"")
    assert _png_to_data_url(path) is None


def test_build_reviewer_input_text_only_when_no_images(tmp_path: Path) -> None:
    result = _build_reviewer_input(
        payload={"spec": {"kind": "cube"}},
        render_sheet=None,
        reference_image=None,
    )
    # Plain string fallback — the SDK accepts this shape for text-only input.
    assert isinstance(result, str)
    assert "ReviewSummary" in result
    assert "cube" in result


def test_build_reviewer_input_multimodal_when_render_sheet_present(tmp_path: Path) -> None:
    sheet = _write_png(tmp_path / "sheet.png", b"render-bytes")
    result = _build_reviewer_input(
        payload={"spec": {"kind": "gear", "teeth": 20}},
        render_sheet=sheet,
        reference_image=None,
    )
    assert isinstance(result, list)
    assert len(result) == 1
    msg = result[0]
    assert msg["role"] == "user"
    parts = msg["content"]
    # Header text + label + image block.
    kinds = [p["type"] for p in parts]
    assert kinds.count("input_image") == 1
    assert kinds.count("input_text") >= 2
    # The image block has a real data URL with the PNG bytes.
    image_parts = [p for p in parts if p["type"] == "input_image"]
    assert image_parts[0]["image_url"].startswith("data:image/png;base64,")
    b64 = image_parts[0]["image_url"].split(",", 1)[1]
    assert base64.b64decode(b64) == _PNG_HEADER + b"render-bytes"


def test_build_reviewer_input_includes_reference_image_when_given(tmp_path: Path) -> None:
    sheet = _write_png(tmp_path / "sheet.png", b"s")
    ref = _write_png(tmp_path / "ref.png", b"r")
    result = _build_reviewer_input(
        payload={"spec": {}},
        render_sheet=sheet,
        reference_image=ref,
    )
    assert isinstance(result, list)
    parts = result[0]["content"]
    image_parts = [p for p in parts if p["type"] == "input_image"]
    # Two images: render sheet first, reference second.
    assert len(image_parts) == 2
    # Each labelled so the model knows which is which.
    text_parts = [p for p in parts if p["type"] == "input_text"]
    blob = " ".join(p["text"] for p in text_parts).lower()
    assert "render sheet" in blob
    assert "reference" in blob


def test_build_reviewer_input_reference_image_only(tmp_path: Path) -> None:
    """Edge case: render sheet missing but a reference image is present.

    The reviewer should still get multimodal input so it can at least compare
    the notes against what the user asked for — better than no image at all.
    """

    ref = _write_png(tmp_path / "ref.png", b"r")
    result = _build_reviewer_input(
        payload={"spec": {}},
        render_sheet=None,
        reference_image=ref,
    )
    assert isinstance(result, list)
    kinds = [p["type"] for p in result[0]["content"]]
    assert "input_image" in kinds
