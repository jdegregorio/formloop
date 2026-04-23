"""Helpers for SDK multimodal message construction.

REQ: FLH-D-004
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any, Sequence


def image_file_to_input_image(path: Path) -> dict[str, str] | None:
    """Convert a local image file into an SDK ``input_image`` content item.

    Returns ``None`` when the file does not exist so callers can build payloads
    without special-case branching.
    """

    if not path.is_file():
        return None
    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"}


def text_and_image_list_to_sdk_message_payload(
    items: Sequence[str | Path],
) -> list[dict[str, Any]]:
    """Build a single-user-message SDK payload while preserving item order.

    ``str`` items become ``input_text`` entries. ``Path`` items become
    ``input_image`` entries when the file exists.
    """

    content: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, str):
            content.append({"type": "input_text", "text": item})
            continue
        image_item = image_file_to_input_image(item)
        if image_item:
            content.append(image_item)

    return [{"role": "user", "content": content}]
