"""Credential models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    """Resolved credentials for one WhatsApp tenant.

    Attributes:
        access_token: Meta access token.
        phone_number_id: Sender phone number ID.
        tenant_id: Application-level tenant identifier.
        app_secret: Optional app secret for webhook verification.
    """

    access_token: str = Field(min_length=1)
    phone_number_id: str = Field(min_length=1)
    tenant_id: Optional[str] = None
    app_secret: Optional[str] = None

    def __repr__(self) -> str:
        """Return a secret-free representation.

        Returns:
            Representation with secrets redacted.
        """
        return (
            f"Credentials(phone_number_id={self.phone_number_id!r}, "
            f"tenant_id={self.tenant_id!r}, access_token='***', app_secret='***')"
        )
