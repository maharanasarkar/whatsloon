"""v26.0 Graph API adapter (pinned current)."""

from __future__ import annotations

from typing import Any

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.config.capabilities import VersionCapabilities


class V26Adapter(VersionAdapter):
    """Compatibility layer for Graph API ``v26.0``.

    Attributes:
        api_version: Pinned current version.
        capabilities: Calls, groups, and Direct Send enabled.
    """

    api_version: str = "v26.0"
    capabilities: VersionCapabilities = VersionCapabilities(
        calls=True, groups=True, direct_send=True
    )

    def build_text_payload(
        self, *, to: str, body: str, preview_url: bool = False
    ) -> dict[str, Any]:
        """Serialize a text message for ``v26.0``.

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


__all__ = ["V26Adapter"]
