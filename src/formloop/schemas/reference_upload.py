"""Reference-image upload response contract for browser UI clients.

REQ: FLU-F-010, FLU-D-008
"""

from __future__ import annotations

from ._common import SchemaModel


class ReferenceImageUploadResponse(SchemaModel):
    """Server-side reference-image handle returned after upload validation."""

    upload_id: str
    reference_image: str
    filename: str
    content_type: str
    size_bytes: int
