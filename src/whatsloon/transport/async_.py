"""Asynchronous pooled transport."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from whatsloon.exceptions import WhatsAppError
from whatsloon.transport.base import (
    BaseTransport,
    backoff_seconds,
    logger,
    map_httpx_error,
    redact_headers,
    should_retry,
    translate_error,
)
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response


class AsyncTransport(BaseTransport):
    """Pooled async transport reusing one ``httpx.AsyncClient``.

    Use as an async context manager for explicit lifecycle management.

    Examples:
        >>> async with AsyncTransport(base_url=..., access_token=..., timeout=..., retry=...) as t:
        ...     response = await t.send(request)
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the async transport.

        Args:
            **kwargs: Forwarded to :class:`BaseTransport`.
        """
        super().__init__(**kwargs)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> AsyncTransport:
        """Enter the transport context, creating the pooled client.

        Returns:
            This transport.
        """
        timeout = httpx.Timeout(
            connect=self.timeout.connect,
            read=self.timeout.read,
            write=self.timeout.write,
            pool=self.timeout.pool,
        )
        self._client = httpx.AsyncClient(timeout=timeout)
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        """Exit the transport context, closing pooled connections."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the pooled client.

        Safe to call multiple times.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _require_client(self) -> httpx.AsyncClient:
        """Return the active client or raise a configuration error.

        Returns:
            Active ``httpx.AsyncClient``.

        Raises:
            ConfigurationError: If used outside the async context.
        """
        from whatsloon.exceptions import ConfigurationError

        if self._client is None:
            raise ConfigurationError("AsyncTransport must be used as an async context manager.")
        return self._client

    def send(self, request: Request) -> Any:
        """Describe async usage; actual execution uses :meth:`asend`.

        Args:
            request: Outbound request.

        Raises:
            ConfigurationError: Always; use ``asend`` instead.
        """
        from whatsloon.exceptions import ConfigurationError

        raise ConfigurationError("AsyncTransport requires 'await transport.asend(request)'.")

    async def asend(self, request: Request) -> Response:
        """Execute one request with retries.

        Args:
            request: Outbound request.

        Returns:
            Normalized response.

        Raises:
            WhatsAppError: On transport failure or Meta rejection.
        """
        last_error: WhatsAppError | None = None
        for attempt in range(self.retry.max_attempts):
            try:
                return await self._send_once(request)
            except WhatsAppError as exc:
                last_error = exc
                if not should_retry(exc, attempt, self.retry):
                    raise
                wait = backoff_seconds(exc, attempt, self.retry)
                logger.debug(
                    "Retrying %s %s (attempt %d) in %.2fs",
                    request.method,
                    request.path,
                    attempt + 2,
                    wait,
                )
                await asyncio.sleep(wait)
        raise last_error  # type: ignore[misc]

    async def _send_once(self, request: Request) -> Response:
        """Execute a single attempt without retry.

        Args:
            request: Outbound request.

        Returns:
            Normalized response.

        Raises:
            WhatsAppError: On transport failure or Meta rejection.
        """
        timeout = None
        if request.timeout_override:
            timeout = httpx.Timeout(
                connect=self.timeout.connect,
                read=request.timeout_override,
                write=self.timeout.write,
                pool=self.timeout.pool,
            )
        headers = self._headers(request.headers)
        if request.files is not None:
            headers.pop("Content-Type", None)
        logger.debug(
            "%s %s headers=%s correlation_id=%s",
            request.method,
            request.path,
            redact_headers(headers),
            request.correlation_id,
        )
        try:
            raw = await self._require_client().request(
                request.method,
                self._url(request.path),
                params=request.params or None,
                json=request.json_body,
                files=request.files,
                data=request.form_data or None,
                headers=headers,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            raise map_httpx_error(exc) from exc
        try:
            data = raw.json() if raw.content else {}
        except ValueError:
            data = {}
        response = Response(
            status_code=raw.status_code,
            data=data if isinstance(data, dict) else {},
            content=raw.content,
            headers=dict(raw.headers),
            correlation_id=request.correlation_id,
        )
        if raw.status_code >= 400:
            raise translate_error(
                status_code=raw.status_code,
                payload=response.data,
                headers=response.headers,
            )
        return response


__all__ = ["AsyncTransport"]
