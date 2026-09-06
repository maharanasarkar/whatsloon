"""In-memory fakes exercising the real client stack.

Fakes run the genuine serialization, adapter, and transport layers against
scripted responses, so tests prove behavior instead of mocking it away.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from whatsloon.client import WhatsApp
from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.transport.response import Response
from whatsloon.transport.sync import SyncTransport


class FakeTransport(SyncTransport):
    """Scripted transport recording every request.

    Attributes:
        script: Queue of response bodies or exceptions, consumed per send.
        seen: Recorded requests in order.
    """

    def __init__(self, script: Optional[list[Any]] = None, **kwargs: Any) -> None:
        """Initialize with a response script.

        Args:
            script: Response bodies (dict) or exceptions, one per send.
            **kwargs: Forwarded to :class:`SyncTransport`.
        """
        kwargs.setdefault("base_url", "https://graph.facebook.com/v26.0")
        kwargs.setdefault("access_token", "fake-token")
        kwargs.setdefault("timeout", TimeoutConfig())
        kwargs.setdefault("retry", RetryConfig(max_attempts=1))
        super().__init__(**kwargs)
        self.script: list[Any] = list(script or [])
        self.seen: list[Any] = []

    def send(self, request: Any) -> Response:
        """Record and answer from the script.

        Args:
            request: Outbound request.

        Returns:
            Normalized canned response.

        Raises:
            Exception: Scripted exceptions, or AssertionError when empty.
        """
        from whatsloon.exceptions import WhatsAppError

        self.seen.append(request)
        if not self.script:
            raise AssertionError("FakeTransport script exhausted.")
        next_item = self.script.pop(0)
        if isinstance(next_item, BaseException):
            if isinstance(next_item, WhatsAppError):
                raise next_item
            raise next_item
        return Response(status_code=200, data=next_item, correlation_id=request.correlation_id)


def make_fake_client(
    script: Optional[list[Any]] = None, **kwargs: Any
) -> tuple[WhatsApp, FakeTransport]:
    """Build a v3 client over a scripted transport.

    Args:
        script: Response bodies or exceptions, one per send.
        **kwargs: Forwarded to :class:`WhatsApp`.

    Returns:
        Tuple of client and fake transport.
    """
    fake = FakeTransport(script)
    kwargs.setdefault("access_token", "fake-token")
    kwargs.setdefault("phone_number_id", "123")
    return WhatsApp(transport=fake, **kwargs), fake


class MockMetaServer:
    """httpx-level fake Meta server with default route fixtures.

    Attributes:
        requests: Recorded httpx requests.
        routes: Mutable mapping of path suffix to handler.
    """

    def __init__(self) -> None:
        """Initialize default routes."""
        self.requests: list[httpx.Request] = []
        self.routes: dict[str, Any] = {
            "/messages": {"messages": [{"id": "wamid.mock-1"}]},
            "/media": {"id": "mock-media-1"},
        }

    def handler(self, request: httpx.Request) -> httpx.Response:
        """Serve one request from routes.

        Args:
            request: Incoming httpx request.

        Returns:
            Canned response; unknown paths return Meta-style errors.
        """
        self.requests.append(request)
        for suffix, body in self.routes.items():
            if request.url.path.endswith(suffix):
                return httpx.Response(200, json=body, request=request)
        return httpx.Response(
            404,
            json={"error": {"message": "Not found", "type": "OAuthException", "code": 803}},
            request=request,
        )

    def transport(self, **kwargs: Any) -> SyncTransport:
        """Build a sync transport bound to this server.

        Args:
            **kwargs: Transport overrides.

        Returns:
            Transport using a MockTransport client.
        """
        transport = SyncTransport(
            base_url=kwargs.get("base_url", "https://graph.facebook.com/v26.0"),
            access_token=kwargs.get("access_token", "fake-token"),
            timeout=kwargs.get("timeout", TimeoutConfig()),
            retry=kwargs.get("retry", RetryConfig(max_attempts=1)),
        )
        transport._client = httpx.Client(transport=httpx.MockTransport(self.handler))
        return transport


__all__ = ["FakeTransport", "MockMetaServer", "make_fake_client"]
