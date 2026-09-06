"""Asynchronous context client sharing domain behavior with sync."""

from __future__ import annotations

from typing import Any, Optional

from whatsloon.api_versions.registry import get_adapter
from whatsloon.auth.credentials import Credentials
from whatsloon.client import (
    SendMessageResult,
    build_text_request,
    normalize_recipient,
    parse_send_result,
)
from whatsloon.config.settings import RetryConfig, TimeoutConfig, WhatsAppConfig
from whatsloon.config.versions import GraphAPIVersion
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response


class AsyncGraphClient:
    """Raw async Graph API escape hatch.

    Attributes:
        transport: Shared pooled async transport.
        phone_number_id: Sender phone number ID.
    """

    def __init__(self, transport: AsyncTransport, phone_number_id: str) -> None:
        """Initialize the raw async client.

        Args:
            transport: Shared pooled async transport.
            phone_number_id: Sender phone number ID.
        """
        self.transport = transport
        self.phone_number_id = phone_number_id

    async def post(self, *, path: str, json: Optional[dict[str, Any]] = None) -> Response:
        """POST an arbitrary versioned Graph API path.

        Args:
            path: URL path beginning with ``/``.
            json: JSON payload.

        Returns:
            Normalized response.
        """
        return await self.transport.asend(Request(method="POST", path=path, json_body=json))

    async def get(self, *, path: str, params: Optional[dict[str, Any]] = None) -> Response:
        """GET an arbitrary versioned Graph API path.

        Args:
            path: URL path beginning with ``/``.
            params: Query parameters.

        Returns:
            Normalized response.
        """
        return await self.transport.asend(Request(method="GET", path=path, params=params or {}))


class AsyncWhatsApp:
    """Asynchronous authenticated API context.

    Shares domain serialization with :class:`WhatsApp`; only the transport
    differs. Must be used as an async context manager.

    Examples:
        >>> async with WhatsApp.async_client(access_token="...", phone_number_id="...") as wa:
        ...     result = await wa.send_text(to="919876543210", body="Hello!")
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
    ) -> None:
        """Initialize the async context client.

        Args:
            access_token: Meta access token.
            phone_number_id: Sender phone number ID.
            graph_api_version: Pinned version or ``"latest"`` alias.
            base_url: Graph API root override (tests, proxies).
            timeout: Timeout budget override.
            retry: Retry policy override.
            tenant_id: Application-level tenant identifier.

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
        self.transport = AsyncTransport(
            base_url=f"{self.config.base_url}/{self.version.value}",
            access_token=access_token,
            timeout=self.config.timeout,
            retry=self.config.retry,
            user_agent=self.config.user_agent,
        )
        self.graph = AsyncGraphClient(self.transport, phone_number_id)
        from whatsloon.business.service import AsyncBusinessService
        from whatsloon.media.service import AsyncMediaService
        from whatsloon.messages.service import AsyncMessageService
        from whatsloon.templates.service import AsyncTemplateService

        self.messages = AsyncMessageService(self.adapter, self.transport, phone_number_id)
        self.media = AsyncMediaService(self.transport, phone_number_id)
        self.templates = AsyncTemplateService(self.transport)
        self.business = AsyncBusinessService(self.transport)
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

    async def __aenter__(self) -> AsyncWhatsApp:
        """Enter the async context, opening pooled connections.

        Returns:
            This client.
        """
        await self.transport.__aenter__()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        """Exit the async context, closing pooled connections."""
        await self.transport.__aexit__(*exc_info)

    async def send_text(
        self, *, to: str, body: str, preview_url: bool = False
    ) -> SendMessageResult:
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
        response = await self.transport.asend(request)
        return parse_send_result(self.adapter, to=normalize_recipient(to), response=response)

    def __repr__(self) -> str:
        """Return a secret-free representation.

        Returns:
            Representation without the access token.
        """
        return (
            f"AsyncWhatsApp(phone_number_id={self.phone_number_id!r}, "
            f"graph_api_version={self.version.value!r})"
        )


__all__ = ["AsyncGraphClient", "AsyncWhatsApp"]
