"""Error hierarchy and translation tests."""

import httpx

from whatsloon.config.retry import parse_retry_after
from whatsloon.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServerError,
    TLSProxyError,
    ValidationAPIError,
    WhatsAppError,
)
from whatsloon.transport.base import extract_trace_id, map_httpx_error, translate_error


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


def test_retry_after_parsing_forms():
    """Numeric, millisecond, and HTTP-date Retry-After forms parse."""
    assert parse_retry_after("7") == 7.0
    assert parse_retry_after("120ms") == 0.12
    assert parse_retry_after(None) is None
    assert parse_retry_after("bogus") is None
    assert parse_retry_after("-3") is None
    future = parse_retry_after("Thu, 01 Jan 2099 00:00:00 GMT")
    assert future is not None and future > 0
    assert parse_retry_after("Thu, 01 Jan 2000 00:00:00 GMT") == 0.0


def test_tls_and_proxy_errors_map_to_tls_proxy_error():
    """TLS/proxy failures are non-retryable TLSProxyError."""
    request = httpx.Request("POST", "https://graph.facebook.com/v26.0/x")
    err = map_httpx_error(httpx.ProxyError("proxy refused", request=request))
    assert isinstance(err, TLSProxyError)
    assert err.retryable is False


def test_trace_id_header_variants():
    """Standard request-ID headers resolve as trace IDs."""
    assert extract_trace_id({"X-FB-Request-ID": "a"}) == "a"
    assert extract_trace_id({"X-Request-Id": "b"}) == "b"
    assert extract_trace_id({"X-Fb-Trace-Id": "c"}) == "c"
    assert extract_trace_id({}) is None
