"""Webhook authenticity verification.

Signatures use HMAC-SHA256 over the raw request body and are compared in
constant time. Every failure mode raises; there is no lenient path.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Optional, Union


def compute_signature(app_secret: Union[str, bytes], raw_body: bytes) -> str:
    """Compute the Meta signature header value for a body.

    Args:
        app_secret: App secret (never logged).
        raw_body: Raw request bytes.

    Returns:
        Header value in ``sha256=<hex>`` form.
    """
    key = app_secret.encode("utf-8") if isinstance(app_secret, str) else app_secret
    digest = hmac.new(key, raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(
    app_secret: Optional[Union[str, bytes]],
    raw_body: bytes,
    signature_header: Optional[str],
) -> None:
    """Verify a Meta webhook signature, failing closed.

    Args:
        app_secret: Configured app secret; None fails closed.
        raw_body: Raw request bytes exactly as received.
        signature_header: Value of ``X-Hub-Signature-256``.

    Raises:
        ConfigurationError: If no app secret is configured.
        InvalidSignatureError: If the header is missing, malformed, or
            does not match in constant-time comparison.
    """
    from whatsloon.exceptions import ConfigurationError, InvalidSignatureError

    if not app_secret:
        raise ConfigurationError("Webhook verification requires an app secret.")
    if not signature_header or not signature_header.startswith("sha256="):
        raise InvalidSignatureError("Missing or malformed X-Hub-Signature-256 header.")
    expected = compute_signature(app_secret, raw_body)
    if not hmac.compare_digest(expected, signature_header):
        raise InvalidSignatureError("Webhook signature mismatch.")


def verify_handshake(
    *,
    mode: Optional[str],
    verify_token_expected: str,
    verify_token_received: Optional[str],
    challenge: Optional[str],
) -> str:
    """Validate a Meta webhook subscription handshake.

    Args:
        mode: The ``hub.mode`` query value.
        verify_token_expected: Configured verify token.
        verify_token_received: The ``hub.verify_token`` query value.
        challenge: The ``hub.challenge`` query value.

    Returns:
        Challenge to echo back on success.

    Raises:
        InvalidPayloadError: If mode, token, or challenge is invalid.
    """
    from whatsloon.exceptions import InvalidPayloadError

    if mode != "subscribe":
        raise InvalidPayloadError(f"Unexpected webhook handshake mode: {mode!r}.")
    if not verify_token_received or verify_token_received != verify_token_expected:
        raise InvalidPayloadError("Webhook verify token mismatch.")
    if not challenge:
        raise InvalidPayloadError("Webhook handshake challenge is missing.")
    return challenge


__all__ = ["compute_signature", "verify_handshake", "verify_signature"]
