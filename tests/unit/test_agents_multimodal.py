"""Unit tests for the multi-modal reviewer message helper.

REQ: FLH-F-007, FLH-F-010 — the Quality Specialist review is multi-modal.
"""

from __future__ import annotations

import base64
from pathlib import Path

from formloop.agents.common import (
    build_multimodal_user_message,
    encode_image_data_url,
)


def _write_png(path: Path) -> Path:
    # A tiny valid-ish PNG header is enough; we never decode, only base64 it.
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes")
    return path


def test_encode_image_data_url_uses_png_mime(tmp_path: Path) -> None:
    p = _write_png(tmp_path / "front.png")
    url = encode_image_data_url(p)
    assert url.startswith("data:image/png;base64,")
    payload = url.split(",", 1)[1]
    assert base64.b64decode(payload) == p.read_bytes()


def test_encode_image_data_url_jpeg_suffix(tmp_path: Path) -> None:
    p = tmp_path / "ref.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")
    url = encode_image_data_url(p)
    assert url.startswith("data:image/jpeg;base64,")


def test_build_multimodal_user_message_text_only() -> None:
    msg = build_multimodal_user_message(text="hello", image_paths=[])
    assert msg == [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        }
    ]


def test_build_multimodal_user_message_attaches_existing_images(tmp_path: Path) -> None:
    ref = _write_png(tmp_path / "ref.png")
    sheet = _write_png(tmp_path / "sheet.png")
    iso = _write_png(tmp_path / "iso.png")

    msg = build_multimodal_user_message(
        text="body",
        image_paths=[
            ("REFERENCE IMAGE:", ref),
            ("RENDER SHEET:", sheet),
            ("ISO VIEW:", iso),
        ],
    )
    assert len(msg) == 1
    content = msg[0]["content"]
    # 1 text + (caption + image) * 3
    assert len(content) == 1 + 2 * 3
    assert content[0] == {"type": "input_text", "text": "body"}

    captions = [c["text"] for c in content if c["type"] == "input_text"][1:]
    assert captions == ["REFERENCE IMAGE:", "RENDER SHEET:", "ISO VIEW:"]

    images = [c for c in content if c["type"] == "input_image"]
    assert len(images) == 3
    for img in images:
        assert img["detail"] == "auto"
        assert img["image_url"].startswith("data:image/png;base64,")


def test_build_multimodal_user_message_skips_missing_files(tmp_path: Path) -> None:
    sheet = _write_png(tmp_path / "sheet.png")
    missing = tmp_path / "does-not-exist.png"

    msg = build_multimodal_user_message(
        text="body",
        image_paths=[
            ("RENDER SHEET:", sheet),
            ("GHOST VIEW:", missing),
        ],
    )
    content = msg[0]["content"]
    captions = [c["text"] for c in content if c["type"] == "input_text"]
    # Only the real image's caption survives (plus the leading body text).
    assert captions == ["body", "RENDER SHEET:"]
    assert sum(1 for c in content if c["type"] == "input_image") == 1
