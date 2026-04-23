"""Unit tests for shared multimodal payload helpers.

REQ: FLH-V-001, FLH-D-004
"""

from __future__ import annotations

import base64
from pathlib import Path

from formloop.runtime.multimodal import (
    image_file_to_input_image,
    text_and_image_list_to_sdk_message_payload,
)


def test_image_file_to_input_image_missing_path_returns_none(tmp_path: Path) -> None:
    missing = tmp_path / "missing.png"
    assert image_file_to_input_image(missing) is None


def test_image_file_to_input_image_mime_falls_back_to_png(tmp_path: Path) -> None:
    image = tmp_path / "blob.unknownext"
    image.write_bytes(b"abc123")

    item = image_file_to_input_image(image)

    assert item is not None
    assert item["type"] == "input_image"
    assert item["image_url"].startswith("data:image/png;base64,")
    encoded = item["image_url"].split(",", 1)[1]
    assert base64.b64decode(encoded) == b"abc123"


def test_text_and_image_list_ordering_is_stable_for_mixed_content(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"1")
    second.write_bytes(b"2")

    payload = text_and_image_list_to_sdk_message_payload(
        ["alpha", first, "beta", second, "gamma"]
    )

    assert len(payload) == 1
    assert payload[0]["role"] == "user"
    content = payload[0]["content"]
    assert [item["type"] for item in content] == [
        "input_text",
        "input_image",
        "input_text",
        "input_image",
        "input_text",
    ]
    assert content[0]["text"] == "alpha"
    assert content[2]["text"] == "beta"
    assert content[4]["text"] == "gamma"
