"""Business account and phone number models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class WhatsAppBusinessAccount(BaseModel):
    """WhatsApp Business Account summary.

    Attributes:
        id: WABA identifier.
        name: Account name when reported.
        timezone_id: Timezone when reported.
    """

    model_config = {"extra": "allow"}

    id: str = ""
    name: Optional[str] = None
    timezone_id: Optional[str] = None


class PhoneNumber(BaseModel):
    """WhatsApp business phone number summary.

    Attributes:
        id: Phone number ID.
        display_phone_number: Display number.
        verified_name: Verified business name.
        quality_rating: Quality rating when reported.
        code_verification_status: Verification status when reported.
    """

    model_config = {"extra": "allow"}

    id: str = ""
    display_phone_number: str = ""
    verified_name: Optional[str] = None
    quality_rating: Optional[str] = None
    code_verification_status: Optional[str] = None
