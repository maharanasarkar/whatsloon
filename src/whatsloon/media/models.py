"""Media resource models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MediaInfo(BaseModel):
    """Media descriptor returned by Meta.

    Attributes:
        id: Media identifier.
        url: Temporary download URL (expires in ~5 minutes).
        mime_type: MIME type when reported.
        sha256: Content hash when reported.
        file_size: Size in bytes when reported.
        messaging_product: Always ``"whatsapp"``.
    """

    id: str = ""
    url: str = ""
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    file_size: Optional[int] = None
    messaging_product: str = "whatsapp"


class UploadResult(BaseModel):
    """Result of a media upload.

    Attributes:
        media_id: Identifier for use in messages.
        mime_type: Uploaded MIME type.
        filename: Uploaded filename.
    """

    media_id: str
    mime_type: str = ""
    filename: str = ""


class MediaDownload(BaseModel):
    """Downloaded media bytes with metadata.

    Attributes:
        content: Raw media bytes.
        mime_type: MIME type when reported.
        sha256: Content hash when reported.
    """

    model_config = {"arbitrary_types_allowed": True}

    content: bytes = Field(default=b"")
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
