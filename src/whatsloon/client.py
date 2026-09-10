"""Synchronous context client and shared domain operations."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.api_versions.registry import get_adapter
from whatsloon.auth.credentials import Credentials
from whatsloon.config.settings import RetryConfig, TimeoutConfig, WhatsAppConfig
from whatsloon.config.versions import GraphAPIVersion
from whatsloon.exceptions import ValidationError
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response
from whatsloon.transport.sync import SyncTransport


class SendMessageResult(BaseModel):
    """Typed result of a send-message operation.

    Attributes:
        message_id: Meta message identifier, if returned.
        to: Destination identifier the message was sent to.
        api_version: Graph API version used.
        correlation_id: Request correlation ID for tracing.
        raw: Preserved Meta response body.
    """

    model_config = {"arbitrary_types_allowed": True}

    message_id: Optional[str] = None
    to: str = ""
    api_version: str = ""
    correlation_id: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


def normalize_recipient(to: str) -> str:
    """Normalize a destination identifier.

    Args:
        to: Destination such as ``"919876543210"`` or ``"+91 98765 43210"``.

    Returns:
        Digits-only international identifier.

    Raises:
        ValidationError: If no digits remain after normalization.
    """
    digits = "".join(char for char in to if char.isdigit())
    if not digits:
        raise ValidationError(f"Invalid recipient identifier: {to!r}.")
    return digits


def build_text_request(
    adapter: VersionAdapter, *, phone_number_id: str, to: str, body: str, preview_url: bool = False
) -> Request:
    """Build a version-specific text send request (transport-agnostic).

    Args:
        adapter: Version adapter for serialization.
        phone_number_id: Sender phone number ID.
        to: Destination identifier.
        body: UTF-8 message body.
        preview_url: Whether URLs generate link previews.

    Returns:
        Transport-ready request shared by sync and async clients.

    Raises:
        ValidationError: If the body is empty or over Meta limits.
    """
    if not body or not body.strip():
        raise ValidationError("Message body must not be empty.")
    if len(body) > 4096:
        raise ValidationError("Message body exceeds 4096 characters.")
    payload = adapter.build_text_payload(
        to=normalize_recipient(to), body=body, preview_url=preview_url
    )
    return Request(
        method="POST",
        path=adapter.messages_path(phone_number_id),
        json_body=payload,
    )


def parse_send_result(adapter: VersionAdapter, *, to: str, response: Response) -> SendMessageResult:
    """Normalize a send response into a typed result.

    Args:
        adapter: Version adapter for normalization.
        to: Destination identifier.
        response: Normalized transport response.

    Returns:
        Typed send result.
    """
    normalized = adapter.normalize_send_result(response.data)
    return SendMessageResult(
        message_id=normalized.get("message_id"),
        to=to,
        api_version=adapter.api_version,
        correlation_id=response.correlation_id,
        raw=normalized.get("raw", {}),
    )


class GraphClient:
    """Raw Graph API escape hatch for unsupported Meta capabilities.

    Attributes:
        transport: Shared pooled transport.
        phone_number_id: Sender phone number ID.
    """

    def __init__(self, transport: SyncTransport, phone_number_id: str) -> None:
        """Initialize the raw client.

        Args:
            transport: Shared pooled transport.
            phone_number_id: Sender phone number ID.
        """
        self.transport = transport
        self.phone_number_id = phone_number_id

    def post(self, *, path: str, json: Optional[dict[str, Any]] = None) -> Response:
        """POST an arbitrary versioned Graph API path.

        Args:
            path: URL path beginning with ``/``.
            json: JSON payload.

        Returns:
            Normalized response.

        Examples:
            >>> client.graph.post(path=f"/{pid}/messages", json=payload)
        """
        return self.transport.send(Request(method="POST", path=path, json_body=json))

    def get(self, *, path: str, params: Optional[dict[str, Any]] = None) -> Response:
        """GET an arbitrary versioned Graph API path.

        Args:
            path: URL path beginning with ``/``.
            params: Query parameters.

        Returns:
            Normalized response.
        """
        return self.transport.send(Request(method="GET", path=path, params=params or {}))


class WhatsApp:
    """Synchronous authenticated API context.

    The client holds credentials and a pinned version, never a permanent
    recipient. Long-lived instances reuse pooled connections.

    Examples:
        >>> wa = WhatsApp(access_token="...", phone_number_id="...")
        >>> result = wa.send_text(to="919876543210", body="Hello!")
        >>> print(result.message_id)
        >>> wa.close()
    """

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        *,
        graph_api_version: str = "latest",
        base_url: Optional[str] = None,
        timeout: Optional[TimeoutConfig] = None,
        retry: Optional[RetryConfig] = None,
        tenant_id: Optional[str] = None,
        transport: Optional[SyncTransport] = None,
        middleware: Optional[list[Any]] = None,
    ) -> None:
        """Initialize the context client.

        Args:
            access_token: Meta access token.
            phone_number_id: Sender phone number ID.
            graph_api_version: Pinned version or ``"latest"`` alias.
            base_url: Graph API root override (tests, proxies).
            timeout: Timeout budget override.
            retry: Retry policy override.
            tenant_id: Application-level tenant identifier.
            transport: Injected transport (tests, custom pooling).
            middleware: Observers for the owned transport; ignored when a
                transport is injected (attach there instead).

        Raises:
            ConfigurationError: If the version or credentials are invalid.
        """
        self.config = WhatsAppConfig(
            access_token=access_token,
            phone_number_id=phone_number_id,
            graph_api_version=graph_api_version,
            tenant_id=tenant_id,
            timeout=timeout or TimeoutConfig(),
            retry=retry or RetryConfig(),
        )
        if base_url:
            self.config.base_url = base_url
        self.version = GraphAPIVersion(self.config.graph_api_version)
        self.adapter = get_adapter(self.version.value)
        self._owns_transport = transport is None
        self.transport = transport or SyncTransport(
            base_url=f"{self.config.base_url}/{self.version.value}",
            access_token=access_token,
            timeout=self.config.timeout,
            retry=self.config.retry,
            user_agent=self.config.user_agent,
            middleware=middleware,
        )
        self.graph = GraphClient(self.transport, phone_number_id)
        from whatsloon.business.service import BusinessService
        from whatsloon.calls.service import CallService
        from whatsloon.groups.service import GroupService
        from whatsloon.media.service import MediaService
        from whatsloon.messages.service import MessageService
        from whatsloon.templates.service import TemplateService

        self.messages = MessageService(self.adapter, self.transport, phone_number_id)
        self.media = MediaService(self.transport, phone_number_id)
        self.templates = TemplateService(self.transport)
        self.business = BusinessService(self.transport)
        self.groups = GroupService(self.transport, phone_number_id)
        self.calls = CallService(self.transport, phone_number_id)
        self.credentials = Credentials(
            access_token=access_token,
            phone_number_id=phone_number_id,
            tenant_id=tenant_id,
        )

    @property
    def phone_number_id(self) -> str:
        """Return the sender phone number ID.

        Returns:
            Sender phone number ID.
        """
        return self.config.phone_number_id

    @classmethod
    def async_client(cls, *args: Any, **kwargs: Any) -> Any:
        """Create the async variant of this context.

        Args:
            *args: Forwarded to :class:`AsyncWhatsApp`.
            **kwargs: Forwarded to :class:`AsyncWhatsApp`.

        Returns:
            Async client usable as an async context manager.
        """
        from whatsloon.async_client import AsyncWhatsApp

        return AsyncWhatsApp(*args, **kwargs)

    def send_text(self, *, to: str, body: str, preview_url: bool = False) -> SendMessageResult:
        """Send a text message to a WhatsApp user.

        Args:
            to: Destination identifier in international format.
            body: UTF-8 message body (1-4096 chars).
            preview_url: Whether URLs generate link previews.

        Returns:
            Typed result with the Meta message identifier.

        Raises:
            ValidationError: If the destination or body is invalid.
            RateLimitError: If Meta throttles the request.
            AuthenticationError: If credentials are invalid.
            WhatsAppAPIError: If Meta rejects the request.
            TransportError: If the request cannot be completed.
        """
        request = build_text_request(
            self.adapter,
            phone_number_id=self.phone_number_id,
            to=to,
            body=body,
            preview_url=preview_url,
        )
        response = self.transport.send(request)
        return parse_send_result(self.adapter, to=normalize_recipient(to), response=response)

    def close(self) -> None:
        """Close pooled connections owned by this client."""
        if self._owns_transport:
            self.transport.close()

    def __enter__(self) -> WhatsApp:
        """Enter the client context.

        Returns:
            This client.
        """
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Exit the client context, closing owned connections."""
        self.close()

    def __repr__(self) -> str:
        """Return a secret-free representation.

        Returns:
            Representation without the access token.
        """
        return (
            f"WhatsApp(phone_number_id={self.phone_number_id!r}, "
            f"graph_api_version={self.version.value!r})"
        )


__all__ = [
    "GraphClient",
    "SendMessageResult",
    "WhatsApp",
    "build_text_request",
    "normalize_recipient",
    "parse_send_result",
]
