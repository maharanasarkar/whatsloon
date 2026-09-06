"""v19.0 Graph API adapter (legacy baseline)."""

from __future__ import annotations

from typing import Any

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.config.capabilities import VersionCapabilities


class V19Adapter(VersionAdapter):
    """Compatibility layer for Graph API ``v19.0``.

    This adapter is frozen as the legacy baseline: later refactors must not
    mutate its historical request/response behavior.
    """

    api_version: str = "v19.0"
    capabilities: VersionCapabilities = VersionCapabilities()

    def build_text_payload(
        self, *, to: str, body: str, preview_url: bool = False
    ) -> dict[str, Any]:
        """Serialize a text message for ``v19.0``.

        Args:
            to: Destination identifier in international format.
            body: UTF-8 message body.
            preview_url: Whether URLs generate link previews.

        Returns:
            Version-specific JSON payload.
        """
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body, "preview_url": preview_url},
        }


__all__ = ["V19Adapter"]
