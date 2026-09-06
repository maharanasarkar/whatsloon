"""2.x compatibility shim.

The legacy mixin-composed API (``WhatsAppCloudAPIClient`` with a pinned
recipient) remains importable while v3 services mature. New code should use
:cls:`whatsloon.client.WhatsApp` instead.

Accessing names through this module emits a :class:`DeprecationWarning`
pointing at the v3 client and migration docs.
"""

from __future__ import annotations

import warnings
from typing import Any

_LEGACY_NAMES = (
    "WhatsAppBaseClient",
    "WhatsAppCloudAPIClient",
    "AddressSender",
    "AudioSender",
    "ContactSender",
    "ContextualReply",
    "CTASender",
    "DocumentSender",
    "FlowSender",
    "ImageSender",
    "ListSender",
    "LocationRequestSender",
    "LocationSender",
    "ReactionSender",
    "ReadMark",
    "ReplyButtonSender",
    "StickerSender",
    "TemplateSender",
    "TextSender",
    "TypingIndicator",
    "VideoSender",
)

__all__ = list(_LEGACY_NAMES)


def __getattr__(name: str) -> Any:
    """Lazily re-export a legacy 2.x name with a deprecation warning.

    Args:
        name: Legacy attribute name.

    Returns:
        The legacy class from the top-level package.

    Raises:
        AttributeError: If the name is not a known legacy export.
    """
    if name not in _LEGACY_NAMES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import whatsloon as root

    warnings.warn(
        f"whatsloon.compat.{name} is deprecated; use whatsloon.client.WhatsApp instead. "
        "See docs/version-support.md and CHANGELOG.md for migration notes.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(root, name)
