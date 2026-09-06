"""Typed exception hierarchy for the WhatsApp SDK.

Every error raised by the v3 core derives from :class:`WhatsAppError`.
``APIError`` and its subclasses preserve Meta diagnostics (HTTP status, Meta
error code/type/message, trace ID, API version) plus a ``retryable`` hint so
callers never parse Meta error strings themselves.

Secrets are never included in messages, ``__repr__``, or logs.
"""

from __future__ import annotations

from typing import Any, Optional


class WhatsAppError(Exception):
    """Base class for all WhatsApp SDK errors."""

    def __init__(self, message: str) -> None:
        """Initialize the error.

        Args:
            message: Human-readable, secret-free description.
        """
        super().__init__(message)
        self.message = message


class ConfigurationError(WhatsAppError):
    """Raised when client configuration is invalid.

    Examples:
        Missing access token, unknown API version, or inconsistent options.
    """


class ValidationError(WhatsAppError):
    """Raised when local input validation fails before any HTTP request.

    Examples:
        Malformed phone identifier, empty message body, or oversized payload.
    """


class TransportError(WhatsAppError):
    """Raised when the HTTP request cannot be completed.

    Attributes:
        retryable: Whether retrying the same request may succeed.
    """

    def __init__(self, message: str, retryable: bool = True) -> None:
        """Initialize the transport error.

        Args:
            message: Human-readable, secret-free description.
            retryable: Whether retrying the same request may succeed.
        """
        super().__init__(message)
        self.retryable = retryable


class ConnectError(TransportError):
    """Raised when the connection to Meta cannot be established."""

    def __init__(self, message: str = "Could not connect to the WhatsApp API.") -> None:
        """Initialize the connection error.

        Args:
            message: Human-readable, secret-free description.
        """
        super().__init__(message, retryable=True)


class TransportTimeoutError(TransportError):
    """Raised when connect, read, write, or pool timeouts are exceeded."""

    def __init__(self, message: str = "Request to the WhatsApp API timed out.") -> None:
        """Initialize the timeout error.

        Args:
            message: Human-readable, secret-free description.
        """
        super().__init__(message, retryable=True)


class TLSProxyError(TransportError):
    """Raised for TLS or proxy failures."""

    def __init__(self, message: str = "TLS/proxy failure contacting the WhatsApp API.") -> None:
        """Initialize the TLS/proxy error.

        Args:
            message: Human-readable, secret-free description.
        """
        super().__init__(message, retryable=False)


class APIError(WhatsAppError):
    """Meta API rejection with structured diagnostics.

    Attributes:
        status_code: HTTP status returned by Meta, if any.
        code: Meta numeric error code, if any.
        error_type: Meta error type string, if any.
        api_version: Graph API version used for the request.
        trace_id: Meta trace/request ID, when supplied.
        retryable: Whether the caller should consider retrying.
        remediation: Actionable next step for the caller.
        raw: Safe raw response metadata (never contains secrets).
    """

    #: Alias kept for ``Raises`` sections written against the spec sketch.
    WhatsAppAPIError = None  # assigned after class definition

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[int] = None,
        error_type: Optional[str] = None,
        api_version: Optional[str] = None,
        trace_id: Optional[str] = None,
        retryable: bool = False,
        remediation: str = "Inspect the error details and retry only if advised.",
        raw: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the API error.

        Args:
            message: Human-readable summary without secrets.
            status_code: HTTP status returned by Meta, if any.
            code: Meta numeric error code, if any.
            error_type: Meta error type string, if any.
            api_version: Graph API version used for the request.
            trace_id: Meta trace/request ID, when supplied.
            retryable: Whether the caller should consider retrying.
            remediation: Actionable next step for the caller.
            raw: Safe raw response metadata (never contains secrets).
        """
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.error_type = error_type
        self.api_version = api_version
        self.trace_id = trace_id
        self.retryable = retryable
        self.remediation = remediation
        self.raw = raw or {}

    def __repr__(self) -> str:
        """Return a secret-free developer representation.

        Returns:
            Developer representation without credentials or tokens.
        """
        return (
            f"{type(self).__name__}(status_code={self.status_code!r}, "
            f"code={self.code!r}, error_type={self.error_type!r}, "
            f"api_version={self.api_version!r}, trace_id={self.trace_id!r})"
        )


#: Backwards-compatible alias for the spec sketch name.
WhatsAppAPIError = APIError
APIError.WhatsAppAPIError = APIError  # type: ignore[attr-defined]


class AuthenticationError(APIError):
    """Raised when credentials are missing, invalid, or expired."""

    def __init__(self, message: str = "Invalid or expired access token.", **kwargs: Any) -> None:
        """Initialize the authentication error.

        Args:
            message: Human-readable summary without secrets.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", False)
        kwargs.setdefault("remediation", "Refresh the access token and retry.")
        super().__init__(message, **kwargs)


class AuthorizationError(APIError):
    """Raised when credentials lack permission for the operation."""

    def __init__(
        self, message: str = "Operation not permitted for these credentials.", **kwargs: Any
    ) -> None:
        """Initialize the authorization error.

        Args:
            message: Human-readable summary without secrets.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", False)
        kwargs.setdefault("remediation", "Check phone number, WABA, and token scopes.")
        super().__init__(message, **kwargs)


class NotFoundError(APIError):
    """Raised when a Meta resource does not exist."""

    def __init__(
        self, message: str = "Requested Meta resource was not found.", **kwargs: Any
    ) -> None:
        """Initialize the not-found error.

        Args:
            message: Human-readable summary without secrets.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", False)
        super().__init__(message, **kwargs)


class ConflictError(APIError):
    """Raised on conflicting state such as duplicate creation."""

    def __init__(
        self, message: str = "Request conflicts with current Meta state.", **kwargs: Any
    ) -> None:
        """Initialize the conflict error.

        Args:
            message: Human-readable summary without secrets.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", False)
        super().__init__(message, **kwargs)


class RateLimitError(APIError):
    """Raised when Meta throttles the application."""

    def __init__(
        self,
        message: str = "Rate limit exceeded.",
        *,
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the rate-limit error.

        Args:
            message: Human-readable summary without secrets.
            retry_after: Seconds suggested by Meta before retrying, if any.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", True)
        kwargs.setdefault("remediation", "Back off and honor Retry-After before retrying.")
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationAPIError(APIError):
    """Raised when Meta rejects the request payload server-side."""

    def __init__(self, message: str = "Meta rejected the request payload.", **kwargs: Any) -> None:
        """Initialize the server-side validation error.

        Args:
            message: Human-readable summary without secrets.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", False)
        super().__init__(message, **kwargs)


class ServerError(APIError):
    """Raised for unexpected Meta server failures (5xx)."""

    def __init__(self, message: str = "Meta API returned a server error.", **kwargs: Any) -> None:
        """Initialize the server error.

        Args:
            message: Human-readable summary without secrets.
            **kwargs: Forwarded to :class:`APIError`.
        """
        kwargs.setdefault("retryable", True)
        super().__init__(message, **kwargs)


class WebhookError(WhatsAppError):
    """Base class for inbound webhook processing failures."""


class InvalidSignatureError(WebhookError):
    """Raised when the Meta webhook signature does not verify."""


class InvalidPayloadError(WebhookError):
    """Raised when a webhook payload cannot be parsed."""


class UnsupportedEventError(WebhookError):
    """Raised when no handler supports a webhook event type."""


class PersistenceError(WhatsAppError):
    """Raised for message/event storage failures."""
