from __future__ import annotations

import base64
import json
from pathlib import Path

from formloop.sdk_messages import build_single_user_multimodal_message


def _write_png(path: Path, payload: bytes) -> None:
    path.write_bytes(payload)


def test_build_single_user_multimodal_message_orders_text_then_images(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    _write_png(first, b"first-bytes")
    _write_png(second, b"second-bytes")

    message = build_single_user_multimodal_message(
        lead_text="Review request",
        payload={"a": 1},
        image_paths=[first, second],
    )

    assert len(message) == 1
    assert message[0]["role"] == "user"

    content = message[0]["content"]
    assert [item["type"] for item in content] == ["input_text", "input_image", "input_image"]
    assert content[0]["text"] == "Review request\n\n" + json.dumps({"a": 1}, indent=2)
    assert content[1]["image_url"].endswith(base64.b64encode(b"first-bytes").decode("ascii"))
    assert content[2]["image_url"].endswith(base64.b64encode(b"second-bytes").decode("ascii"))


def test_build_single_user_multimodal_message_reports_missing_images_deterministically(tmp_path: Path) -> None:
    existing = tmp_path / "exists.png"
    missing_one = tmp_path / "missing-one.png"
    missing_two = tmp_path / "missing-two.png"
    _write_png(existing, b"exists")

    message = build_single_user_multimodal_message(
        lead_text="Judge request",
        payload={"case": "demo"},
        image_paths=[missing_one, existing, missing_two],
    )

    content = message[0]["content"]
    assert [item["type"] for item in content] == ["input_text", "input_image", "input_text"]
    assert "missing-one.png, missing-two.png" in content[-1]["text"]
