"""Shared transport base: error mapping and retry orchestration.

Domain code never touches HTTP directly. Sync and async transports reuse
:func:`should_retry`, :func:`backoff_seconds`, and :func:`translate_error`.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from whatsloon.config.retry import backoff_delay, parse_retry_after
from whatsloon.config.settings import RetryConfig
from whatsloon.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConnectError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TransportError,
    TransportTimeoutError,
    ValidationAPIError,
    WhatsAppError,
)
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response

logger = logging.getLogger("whatsloon.transport")


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Redact authorization material from headers for logging.

    Args:
        headers: Outgoing headers.

    Returns:
        Copy with the ``Authorization`` value replaced.
    """
    redacted = dict(headers)
    if "Authorization" in redacted:
        redacted["Authorization"] = "Bearer ***"
    return redacted


def extract_trace_id(headers: dict[str, str]) -> Optional[str]:
    """Extract a Meta trace/request ID from response headers.

    Args:
        headers: Response headers (case-insensitive keys checked).

    Returns:
        Trace ID when present, else None.
    """
    lowered = {key.lower(): value for key, value in headers.items()}
    for candidate in ("x-fb-trace-id", "x-business-use-case-usage", "facebook-api-version"):
        if candidate in lowered:
            return lowered[candidate]
    return None


def translate_error(
    *,
    status_code: int,
    payload: dict[str, Any],
    headers: dict[str, str],
    api_version: Optional[str] = None,
) -> APIError:
    """Translate a Meta error payload into a typed exception.

    Args:
        status_code: HTTP status code.
        payload: Decoded Meta error body.
        headers: Response headers for trace extraction.
        api_version: Graph API version used.

    Returns:
        Typed :class:`APIError` subclass instance.
    """
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    message = error.get("message", f"Meta API request failed with status {status_code}.")
    code = error.get("code")
    error_type = error.get("type")
    trace_id = extract_trace_id(headers)
    common = {
        "status_code": status_code,
        "code": code if isinstance(code, int) else None,
        "error_type": error_type,
        "api_version": api_version,
        "trace_id": trace_id,
        "raw": {"error": error},
    }
    if status_code == 429:
        retry_after = parse_retry_after(
            {key.lower(): value for key, value in headers.items()}.get("retry-after")
        )
        return RateLimitError(message, retry_after=retry_after, **common)
    if status_code in (401, 403) and code in (190, 102, 10, 200, 299):
        return AuthenticationError(message, **common)
    if status_code in (401, 403):
        return AuthorizationError(message, **common)
    if status_code == 404:
        return NotFoundError(message, **common)
    if status_code == 409:
        return ConflictError(message, **common)
    if status_code == 400:
        return ValidationAPIError(message, **common)
    if status_code >= 500:
        return ServerError(message, **common)
    return APIError(message, **common)


def map_httpx_error(error: Exception) -> TransportError:
    """Map an httpx exception to a typed transport error.

    Args:
        error: The caught httpx exception.

    Returns:
        Typed :class:`TransportError` without secrets.
    """
    if isinstance(error, httpx.ConnectError):
        return ConnectError()
    if isinstance(error, httpx.TimeoutException):
        return TransportTimeoutError()
    if isinstance(error, (httpx.DecodingError, httpx.TooManyRedirects)):
        return TransportError(str(error), retryable=False)
    return TransportError(f"Transport failure: {type(error).__name__}.", retryable=True)


def should_retry(exc: WhatsAppError, attempt: int, policy: RetryConfig) -> bool:
    """Decide whether an operation may be retried.

    Args:
        exc: The failure from the last attempt.
        attempt: Zero-based attempt index just completed.
        policy: Retry policy.

    Returns:
        True when another attempt is allowed.
    """
    if attempt + 1 >= policy.max_attempts:
        return False
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, TransportError):
        return exc.retryable
    return False


def backoff_seconds(exc: WhatsAppError, attempt: int, policy: RetryConfig) -> float:
    """Compute wait time before the next attempt.

    Args:
        exc: The failure from the last attempt.
        attempt: Zero-based attempt index just completed.
        policy: Retry policy.

    Returns:
        Seconds to wait, honoring ``Retry-After`` for rate limits.
    """
    if isinstance(exc, RateLimitError) and policy.honor_retry_after and exc.retry_after:
        return exc.retry_after
    return backoff_delay(attempt, policy)


class BaseTransport(ABC):
    """Shared transport behavior over a versioned base URL.

    Attributes:
        base_url: Root such as ``https://graph.facebook.com/v26.0``.
        access_token: Bearer token (never logged).
        timeout: Timeout budget.
        retry: Retry policy.
    """

    def __init__(
        self,
        *,
        base_url: str,
        access_token: str,
        timeout: Any,
        retry: RetryConfig,
        user_agent: str = "whatsloon/3",
        middleware: Optional[list[Any]] = None,
    ) -> None:
        """Initialize shared transport state.

        Args:
            base_url: Versioned Graph API root.
            access_token: Bearer token.
            timeout: Timeout budget.
            retry: Retry policy.
            user_agent: SDK user-agent header value.
            middleware: Observers invoked per attempt (default none).
        """
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self.timeout = timeout
        self.retry = retry
        self.user_agent = user_agent
        self.middleware: list[Any] = list(middleware or [])

    def _notify_before(self, request: Request) -> None:
        """Invoke before_send on all middleware.

        Args:
            request: Outbound request.
        """
        for observer in self.middleware:
            observer.before_send(request)

    def _notify_after(self, request: Request, response: Response) -> None:
        """Invoke after_send on all middleware.

        Args:
            request: Outbound request.
            response: Normalized response.
        """
        for observer in self.middleware:
            observer.after_send(request, response)

    def _notify_error(self, request: Request, error: Exception) -> None:
        """Invoke record_error where supported.

        Args:
            request: Outbound request.
            error: The failure.
        """
        for observer in self.middleware:
            recorder = getattr(observer, "record_error", None)
            if callable(recorder):
                recorder(request, error)

    def _headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        """Build outgoing headers with auth.

        Args:
            extra: Per-request header overrides.

        Returns:
            Merged headers including authorization.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": self.user_agent,
        }
        if extra:
            headers.update(extra)
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        return headers

    def _url(self, path: str) -> str:
        """Join the base URL and request path.

        Absolute URLs (media download links) pass through unchanged.

        Args:
            path: URL path beginning with ``/``, or an absolute URL.

        Returns:
            Absolute URL.
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}{path}"

    @abstractmethod
    def send(self, request: Request) -> Response:
        """Execute one request with retries.

        Args:
            request: Outbound request.

        Returns:
            Normalized response.

        Raises:
            WhatsAppError: On transport failure or Meta rejection.
        """
        ...  # pragma: no cover
