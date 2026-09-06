"""Transport middleware hooks.

Middleware observes requests/responses for tracing and metrics without ever
seeing secrets: headers are redacted and bodies are never logged here.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from whatsloon.transport.base import redact_headers
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response

logger = logging.getLogger("whatsloon.transport.middleware")


class TransportMiddleware(Protocol):
    """Observe transport calls for tracing or metrics."""

    def before_send(self, request: Request) -> None:
        """Observe an outbound request before execution.

        Args:
            request: Outbound request.
        """
        ...  # pragma: no cover

    def after_send(self, request: Request, response: Response) -> None:
        """Observe a completed request.

        Args:
            request: Outbound request.
            response: Normalized response.
        """
        ...  # pragma: no cover


class LoggingMiddleware:
    """Log request outcomes with redacted headers.

    Attributes:
        logger: Logger used for transport records.
    """

    def __init__(self, logger: Any = logger) -> None:
        """Initialize the middleware.

        Args:
            logger: Logger used for transport records.
        """
        self.logger = logger

    def before_send(self, request: Request) -> None:
        """Log the outgoing request line without body or secrets.

        Args:
            request: Outbound request.
        """
        self.logger.debug(
            "%s %s correlation_id=%s", request.method, request.path, request.correlation_id
        )

    def after_send(self, request: Request, response: Response) -> None:
        """Log the response status line.

        Args:
            request: Outbound request.
            response: Normalized response.
        """
        self.logger.debug(
            "%s %s -> %s correlation_id=%s",
            request.method,
            request.path,
            response.status_code,
            request.correlation_id,
        )


__all__ = ["LoggingMiddleware", "TransportMiddleware", "redact_headers"]
