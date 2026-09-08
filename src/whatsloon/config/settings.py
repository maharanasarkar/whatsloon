"""Client configuration models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TimeoutConfig(BaseModel):
    """HTTP timeout budget in seconds.

    Attributes:
        connect: Seconds to establish a connection.
        read: Seconds to wait for response data.
        write: Seconds to send request data.
        pool: Seconds to wait for a pooled connection.
    """

    connect: float = Field(default=5.0, gt=0)
    read: float = Field(default=15.0, gt=0)
    write: float = Field(default=10.0, gt=0)
    pool: float = Field(default=5.0, gt=0)


class RetryConfig(BaseModel):
    """Retry policy for safe operations.

    Attributes:
        max_attempts: Total attempts including the first try.
        backoff_base: Base seconds for exponential backoff.
        backoff_cap: Maximum backoff seconds between attempts.
        jitter: Whether to add random jitter to backoff.
        honor_retry_after: Whether to honor Meta ``Retry-After`` headers.
    """

    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_base: float = Field(default=0.5, gt=0)
    backoff_cap: float = Field(default=30.0, gt=0)
    jitter: bool = True
    honor_retry_after: bool = True


class WhatsAppConfig(BaseModel):
    """Authenticated API context configuration.

    The client represents credentials plus a pinned Graph API version, never
    a single permanent recipient. Recipients are per-send arguments.

    Attributes:
        access_token: Meta access token (never logged or repr'd).
        phone_number_id: Sender phone number ID.
        graph_api_version: Pinned version or ``"latest"`` alias.
        base_url: Override for the Graph API root (tests, proxies).
        timeout: Timeout budget.
        retry: Retry policy.
        tenant_id: Application-level tenant identifier for multi-tenancy.
        user_agent: SDK user-agent suffix.
    """

    access_token: str = Field(min_length=1)
    phone_number_id: str = Field(min_length=1)
    graph_api_version: str = "latest"
    base_url: str = "https://graph.facebook.com"
    timeout: TimeoutConfig = Field(default_factory=TimeoutConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    tenant_id: Optional[str] = None
    user_agent: str = "whatsloon/3"

    model_config = {"validate_assignment": True}

    def __repr__(self) -> str:
        """Return a secret-free representation.

        Returns:
            Representation with the access token redacted.
        """
        return (
            f"WhatsAppConfig(phone_number_id={self.phone_number_id!r}, "
            f"graph_api_version={self.graph_api_version!r}, "
            f"tenant_id={self.tenant_id!r}, access_token='***')"
        )
