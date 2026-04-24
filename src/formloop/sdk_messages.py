"""Reusable OpenAI SDK message helpers for mixed text+image payloads."""

from __future__ import annotations

import base64
import json
import mimetypes
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def build_input_image_item(path: Path) -> dict[str, str] | None:
    """Return an `input_image` content item for an on-disk image, else None."""

    if not path.is_file():
        return None
    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"}


def build_single_user_multimodal_message(
    *,
    lead_text: str,
    payload: Mapping[str, Any],
    image_paths: Sequence[Path],
) -> list[dict[str, Any]]:
    """Build one user message containing text followed by available images.

    Ordering is deterministic:
    1) lead text + JSON payload
    2) one `input_image` item per existing image path, in input order
    3) optional deterministic note for skipped/missing images
    """

    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": f"{lead_text}\n\n" + json.dumps(payload, indent=2, default=str),
        }
    ]

    skipped_images: list[str] = []
    for image_path in image_paths:
        image_item = build_input_image_item(image_path)
        if image_item is None:
            skipped_images.append(image_path.name)
            continue
        content.append(image_item)

    if skipped_images:
        content.append(
            {
                "type": "input_text",
                "text": "Skipped missing/unreadable images: " + ", ".join(skipped_images),
            }
        )

    return [{"role": "user", "content": content}]
