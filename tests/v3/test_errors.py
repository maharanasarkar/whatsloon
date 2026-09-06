"""Error hierarchy and translation tests."""

from whatsloon.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServerError,
    ValidationAPIError,
    WhatsAppError,
)
from whatsloon.transport.base import translate_error


def test_auth_error_mapping():
    """Meta OAuth failures map to AuthenticationError."""
    err = translate_error(
        status_code=401,
        payload={"error": {"message": "Invalid token", "type": "OAuthException", "code": 190}},
        headers={},
        api_version="v26.0",
    )
    assert isinstance(err, AuthenticationError)
    assert err.code == 190
    assert err.api_version == "v26.0"
    assert err.retryable is False


def test_rate_limit_honors_retry_after():
    """429 maps to RateLimitError with parsed Retry-After."""
    err = translate_error(
        status_code=429,
        payload={"error": {"message": "Slow down", "type": "OAuthException", "code": 4}},
        headers={"Retry-After": "7"},
        api_version="v19.0",
    )
    assert isinstance(err, RateLimitError)
    assert err.retry_after == 7.0
    assert err.retryable is True


def test_server_and_validation_mapping():
    """5xx is retryable ServerError; 400 is ValidationAPIError."""
    server = translate_error(status_code=500, payload={}, headers={})
    assert isinstance(server, ServerError) and server.retryable is True
    invalid = translate_error(
        status_code=400,
        payload={"error": {"message": "Bad param", "type": "OAuthException", "code": 100}},
        headers={},
    )
    assert isinstance(invalid, ValidationAPIError) and invalid.retryable is False
    forbidden = translate_error(status_code=403, payload={}, headers={})
    assert isinstance(forbidden, AuthorizationError)


def test_repr_never_leaks_secrets():
    """Error reprs carry diagnostics, never tokens."""
    err = APIError("boom", status_code=500, trace_id="t-1")
    assert "token" not in repr(err).lower()
    assert "t-1" in repr(err)
    assert isinstance(err, WhatsAppError)
