"""v20.0 Graph API adapter (migration-step baseline)."""

from __future__ import annotations

from typing import Any

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.config.capabilities import VersionCapabilities


class V20Adapter(VersionAdapter):
    """Compatibility layer for Graph API ``v20.0``.

    Frozen as the intermediate migration baseline between v19.0 and v26.0:
    later refactors must not mutate its historical request behavior.
    """

    api_version: str = "v20.0"
    capabilities: VersionCapabilities = VersionCapabilities()

    def build_text_payload(
        self, *, to: str, body: str, preview_url: bool = False
    ) -> dict[str, Any]:
        """Serialize a text message for ``v20.0``.

        Args:
            to: Destination identifier in international format.
            body: UTF-8 message body.
            preview_url: Whether URLs generate link previews.

        Returns:
            Version-specific JSON payload.
        """
        from whatsloon.messages.models import TextMessage
        from whatsloon.messages.serializers import serialize_text

        return serialize_text(to, TextMessage(body=body, preview_url=preview_url))


__all__ = ["V20Adapter"]
