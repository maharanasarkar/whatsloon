"""Media upload/download/delete services over the shared transport."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from whatsloon.exceptions import ValidationError
from whatsloon.media.models import MediaDownload, MediaInfo, UploadResult
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport


def _upload_request(phone_number_id: str, filename: str, content: bytes, mime_type: str) -> Request:
    """Build a multipart media upload request.

    Args:
        phone_number_id: Sender phone number ID.
        filename: Upload filename.
        content: Raw file bytes.
        mime_type: MIME type such as ``"image/jpeg"``.

    Returns:
        Transport-ready multipart request.
    """
    return Request(
        method="POST",
        path=f"/{phone_number_id}/media",
        files={"file": (filename, content, mime_type)},
        form_data={"messaging_product": "whatsapp", "type": mime_type},
    )


class MediaService:
    """Synchronous media operations.

    Attributes:
        transport: Shared pooled transport.
        phone_number_id: Sender phone number ID.
    """

    def __init__(self, transport: SyncTransport, phone_number_id: str) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled transport.
            phone_number_id: Sender phone number ID.
        """
        self.transport = transport
        self.phone_number_id = phone_number_id

    def upload_file(self, path: Union[str, Path], mime_type: str) -> UploadResult:
        """Upload a media file from disk.

        Args:
            path: Local file path.
            mime_type: MIME type such as ``"image/jpeg"``.

        Returns:
            Upload result with the Meta media ID.

        Raises:
            ValidationError: If inputs are invalid or the file is missing.
            WhatsAppAPIError: If Meta rejects the upload.
        """
        file_path = Path(path)
        if not mime_type or "/" not in mime_type:
            raise ValidationError(f"Invalid MIME type: {mime_type!r}.")
        if not file_path.is_file():
            raise ValidationError(f"Media file not found: {file_path}.")
        return self.upload_bytes(file_path.read_bytes(), mime_type, filename=file_path.name)

    def upload_bytes(
        self, content: bytes, mime_type: str, *, filename: str = "upload.bin"
    ) -> UploadResult:
        """Upload media from memory.

        Args:
            content: Raw file bytes.
            mime_type: MIME type such as ``"image/jpeg"``.
            filename: Upload filename.

        Returns:
            Upload result with the Meta media ID.

        Raises:
            ValidationError: If content or MIME type is invalid.
            WhatsAppAPIError: If Meta rejects the upload.
        """
        if not content:
            raise ValidationError("Media content must not be empty.")
        if not mime_type or "/" not in mime_type:
            raise ValidationError(f"Invalid MIME type: {mime_type!r}.")
        request = _upload_request(self.phone_number_id, filename, content, mime_type)
        response = self.transport.send(request)
        return UploadResult(
            media_id=str(response.data.get("id", "")), mime_type=mime_type, filename=filename
        )

    def get_url(self, media_id: str) -> MediaInfo:
        """Retrieve a temporary download URL for uploaded media.

        Args:
            media_id: Meta media identifier.

        Returns:
            Media descriptor with the download URL.
        """
        response = self.transport.send(
            Request(
                method="GET",
                path=f"/{media_id}",
                params={"phone_number_id": self.phone_number_id},
            )
        )
        return MediaInfo(**{k: v for k, v in response.data.items() if k in MediaInfo.model_fields})

    def download(self, media_id: str) -> MediaDownload:
        """Download media bytes via the temporary URL.

        Args:
            media_id: Meta media identifier.

        Returns:
            Media bytes with metadata.
        """
        info = self.get_url(media_id)
        response = self.transport.send(Request(method="GET", path=info.url or f"/{media_id}"))
        return MediaDownload(content=response.content, mime_type=info.mime_type, sha256=info.sha256)

    def delete(self, media_id: str) -> bool:
        """Delete uploaded media.

        Args:
            media_id: Meta media identifier.

        Returns:
            True when Meta confirms deletion.
        """
        response = self.transport.send(Request(method="DELETE", path=f"/{media_id}"))
        return bool(response.data.get("success", response.status_code == 200))


class AsyncMediaService:
    """Asynchronous media operations sharing sync serialization.

    Attributes:
        transport: Shared pooled async transport.
        phone_number_id: Sender phone number ID.
    """

    def __init__(self, transport: AsyncTransport, phone_number_id: str) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled async transport.
            phone_number_id: Sender phone number ID.
        """
        self.transport = transport
        self.phone_number_id = phone_number_id

    async def upload_bytes(
        self, content: bytes, mime_type: str, *, filename: str = "upload.bin"
    ) -> UploadResult:
        """Upload media from memory.

        Args:
            content: Raw file bytes.
            mime_type: MIME type such as ``"image/jpeg"``.
            filename: Upload filename.

        Returns:
            Upload result with the Meta media ID.

        Raises:
            ValidationError: If content or MIME type is invalid.
            WhatsAppAPIError: If Meta rejects the upload.
        """
        if not content:
            raise ValidationError("Media content must not be empty.")
        if not mime_type or "/" not in mime_type:
            raise ValidationError(f"Invalid MIME type: {mime_type!r}.")
        request = _upload_request(self.phone_number_id, filename, content, mime_type)
        response = await self.transport.asend(request)
        return UploadResult(
            media_id=str(response.data.get("id", "")), mime_type=mime_type, filename=filename
        )

    async def get_url(self, media_id: str) -> MediaInfo:
        """Retrieve a temporary download URL for uploaded media.

        Args:
            media_id: Meta media identifier.

        Returns:
            Media descriptor with the download URL.
        """
        response = await self.transport.asend(
            Request(
                method="GET",
                path=f"/{media_id}",
                params={"phone_number_id": self.phone_number_id},
            )
        )
        return MediaInfo(**{k: v for k, v in response.data.items() if k in MediaInfo.model_fields})

    async def delete(self, media_id: str) -> bool:
        """Delete uploaded media.

        Args:
            media_id: Meta media identifier.

        Returns:
            True when Meta confirms deletion.
        """
        response = await self.transport.asend(Request(method="DELETE", path=f"/{media_id}"))
        return bool(response.data.get("success", response.status_code == 200))


__all__ = ["AsyncMediaService", "MediaService"]
