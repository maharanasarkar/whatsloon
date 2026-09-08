"""Business account and phone number services."""

from __future__ import annotations

from whatsloon.business.models import PhoneNumber, WhatsAppBusinessAccount
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport


class BusinessService:
    """Synchronous WABA and phone number operations.

    Attributes:
        transport: Shared pooled transport.
    """

    def __init__(self, transport: SyncTransport) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled transport.
        """
        self.transport = transport

    def get_account(self, waba_id: str) -> WhatsAppBusinessAccount:
        """Fetch a WhatsApp Business Account summary.

        Args:
            waba_id: WhatsApp Business Account ID.

        Returns:
            Account summary.
        """
        response = self.transport.send(Request(method="GET", path=f"/{waba_id}"))
        return WhatsAppBusinessAccount(**response.data)

    def list_phone_numbers(self, waba_id: str) -> list[PhoneNumber]:
        """List phone numbers for a WhatsApp Business Account.

        Args:
            waba_id: WhatsApp Business Account ID.

        Returns:
            Phone number summaries.
        """
        response = self.transport.send(Request(method="GET", path=f"/{waba_id}/phone_numbers"))
        return [PhoneNumber(**item) for item in response.data.get("data", [])]

    def get_phone_number(self, phone_number_id: str) -> PhoneNumber:
        """Fetch one phone number summary.

        Args:
            phone_number_id: Phone number ID.

        Returns:
            Phone number summary.
        """
        response = self.transport.send(Request(method="GET", path=f"/{phone_number_id}"))
        return PhoneNumber(**response.data)

    def register_phone(self, phone_number_id: str, pin: str) -> bool:
        """Register a phone number with its verification PIN.

        Args:
            phone_number_id: Phone number ID.
            pin: Verification PIN.

        Returns:
            True when Meta confirms registration.
        """
        response = self.transport.send(
            Request(
                method="POST",
                path=f"/{phone_number_id}/register",
                json_body={"messaging_product": "whatsapp", "pin": pin},
            )
        )
        return bool(response.data.get("success", response.status_code == 200))

    def deregister_phone(self, phone_number_id: str) -> bool:
        """Deregister a phone number.

        Args:
            phone_number_id: Phone number ID.

        Returns:
            True when Meta confirms deregistration.
        """
        response = self.transport.send(
            Request(method="POST", path=f"/{phone_number_id}/deregister")
        )
        return bool(response.data.get("success", response.status_code == 200))


class AsyncBusinessService:
    """Asynchronous WABA and phone number operations.

    Attributes:
        transport: Shared pooled async transport.
    """

    def __init__(self, transport: AsyncTransport) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled async transport.
        """
        self.transport = transport

    async def list_phone_numbers(self, waba_id: str) -> list[PhoneNumber]:
        """List phone numbers for a WhatsApp Business Account.

        Args:
            waba_id: WhatsApp Business Account ID.

        Returns:
            Phone number summaries.
        """
        response = await self.transport.asend(
            Request(method="GET", path=f"/{waba_id}/phone_numbers")
        )
        return [PhoneNumber(**item) for item in response.data.get("data", [])]

    async def get_phone_number(self, phone_number_id: str) -> PhoneNumber:
        """Fetch one phone number summary.

        Args:
            phone_number_id: Phone number ID.

        Returns:
            Phone number summary.
        """
        response = await self.transport.asend(Request(method="GET", path=f"/{phone_number_id}"))
        return PhoneNumber(**response.data)


__all__ = ["AsyncBusinessService", "BusinessService"]
