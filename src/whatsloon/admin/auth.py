"""Admin authentication and privacy helpers.

Authentication is pluggable: applications provide an :class:`AdminAuth`
implementation. PII masking is on by default; raw payloads require an
explicit privileged role.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

SECRET_KEYS = frozenset(
    {
        "access_token",
        "app_secret",
        "webhook_secret",
        "authorization",
        "token",
        "secret",
        "password",
    }
)
"""Payload keys that are always redacted in admin views."""


def mask_phone(value: str) -> str:
    """Mask a phone identifier, keeping country context.

    Args:
        value: Digits identifier.

    Returns:
        Masked form such as ``"91••••3210"``.
    """
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) <= 4:
        return "••••"
    return f"{digits[:2]}••••{digits[-4:]}"


def mask_text(value: Optional[str], visible: int = 24) -> Optional[str]:
    """Truncate free text for list views.

    Args:
        value: Original text.
        visible: Characters kept before truncation.

    Returns:
        Truncated text or None.
    """
    if value is None:
        return None
    return value if len(value) <= visible else value[:visible] + "…"


def redact_payload(payload: Any) -> Any:
    """Recursively redact secret keys from a payload.

    Args:
        payload: Arbitrary JSON-like data.

    Returns:
        Copy with secret values replaced by ``"***"``.
    """
    if isinstance(payload, dict):
        return {
            key: ("***" if key.lower() in SECRET_KEYS else redact_payload(val))
            for key, val in payload.items()
        }
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    return payload


@dataclass
class AdminUser:
    """An authenticated admin principal.

    Attributes:
        username: Login name.
        tenant_id: Authorized tenant scope; ``"*"`` allows all.
        roles: Role names; ``"owner"`` unlocks privileged raw views.
    """

    username: str
    tenant_id: str = "*"
    roles: list[str] = field(default_factory=lambda: ["viewer"])

    @property
    def can_view_raw(self) -> bool:
        """Whether the user may view redacted raw payloads.

        Returns:
            True for owner/operator roles.
        """
        return "owner" in self.roles or "operator" in self.roles

    def may_access(self, tenant_id: str) -> bool:
        """Check tenant scope.

        Args:
            tenant_id: Requested tenant.

        Returns:
            True when in scope.
        """
        return self.tenant_id == "*" or self.tenant_id == tenant_id


class AdminAuth(Protocol):
    """Pluggable admin authentication."""

    def authenticate(self, token: Optional[str]) -> Optional[AdminUser]:
        """Resolve a bearer token to a principal.

        Args:
            token: Bearer token from the request, if any.

        Returns:
            Principal or None when unauthorized.
        """
        ...  # pragma: no cover


class StaticTokenAuth:
    """Map static bearer tokens to principals (development/small deploys).

    Attributes:
        tokens: Mapping of token to principal.
    """

    def __init__(self, tokens: dict[str, AdminUser]) -> None:
        """Initialize the mapping.

        Args:
            tokens: Mapping of token to principal.
        """
        self._tokens = tokens

    def authenticate(self, token: Optional[str]) -> Optional[AdminUser]:
        """Resolve a bearer token to a principal.

        Args:
            token: Bearer token from the request, if any.

        Returns:
            Principal or None when unauthorized.
        """
        if not token:
            return None
        return self._tokens.get(token)
