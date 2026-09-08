"""Version adapter interface.

All Meta version differences live behind this boundary. Feature code calls
the adapter; it never branches on raw version strings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from whatsloon.config.capabilities import VersionCapabilities
from whatsloon.exceptions import APIError


class VersionAdapter(ABC):
    """Compatibility layer for one Graph API version.

    Attributes:
        api_version: Canonical version string, e.g. ``"v26.0"``.
        capabilities: Feature flags for this version.
    """

    api_version: str = ""
    capabilities: VersionCapabilities = VersionCapabilities()

    def messages_path(self, phone_number_id: str) -> str:
        """Build the send-message path for a sender.

        Args:
            phone_number_id: Sender phone number ID.

        Returns:
            Version-scoped path such as ``/{id}/messages``.
        """
        return f"/{phone_number_id}/messages"

    @abstractmethod
    def build_text_payload(
        self, *, to: str, body: str, preview_url: bool = False
    ) -> dict[str, Any]:
        """Serialize a text message into the version-specific payload.

        Args:
            to: Destination identifier in international format.
            body: UTF-8 message body.
            preview_url: Whether URLs generate link previews.

        Returns:
            Version-specific JSON payload.
        """
        ...  # pragma: no cover

    def normalize_send_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize a send-message response into stable fields.

        Args:
            payload: Decoded Meta response body.

        Returns:
            Mapping with ``message_id`` and ``raw`` keys. Unknown fields in
            the Meta payload are preserved under ``raw``.
        """
        messages = payload.get("messages", [])
        message_id = messages[0].get("id") if messages else None
        return {"message_id": message_id, "raw": payload}

    def translate_error(
        self,
        *,
        status_code: int,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> APIError:
        """Translate a Meta error with version-specific semantics.

        Args:
            status_code: HTTP status code.
            payload: Decoded Meta error body.
            headers: Response headers.

        Returns:
            Typed :class:`APIError` subclass instance.
        """
        from whatsloon.transport.base import translate_error

        return translate_error(
            status_code=status_code,
            payload=payload,
            headers=headers,
            api_version=self.api_version,
        )

    def normalize_webhook_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize a webhook envelope for this version.

        Args:
            payload: Raw webhook JSON.

        Returns:
            Envelope with ``api_version`` stamped and unknown fields kept.
        """
        return {"api_version": self.api_version, "raw": payload}


__all__ = ["VersionAdapter"]
