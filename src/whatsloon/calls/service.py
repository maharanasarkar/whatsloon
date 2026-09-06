"""Voice calling services (Calling API)."""

from __future__ import annotations

from typing import Optional

from whatsloon.calls.models import CallAction, CallPermission, CallSession, CallSettings
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport


class CallService:
    """Synchronous voice call operations.

    Attributes:
        transport: Shared pooled transport.
        phone_number_id: Sender phone number ID.
    """

    def __init__(self, transport: SyncTransport, phone_number_id: str) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled transport.
            phone_number_id: Sender phone number ID.
        """
        self.transport = transport
        self.phone_number_id = phone_number_id

    def act(self, action: CallAction) -> dict:
        """Execute a call action.

        Args:
            action: Validated call action.

        Returns:
            Meta response body.
        """
        response = self.transport.send(
            Request(
                method="POST",
                path=f"/{self.phone_number_id}/calls",
                json_body=action.payload(),
            )
        )
        return response.data

    def connect(
        self, *, to: str, sdp_offer: str, biz_opaque_callback_data: Optional[str] = None
    ) -> dict:
        """Initiate a business-initiated call.

        Args:
            to: Callee identifier.
            sdp_offer: RFC 8866 SDP offer.
            biz_opaque_callback_data: Optional tracking string.

        Returns:
            Meta response body with the call ID.
        """
        return self.act(
            CallAction(
                action="connect",
                to=to,
                session=CallSession(sdp_type="offer", sdp=sdp_offer),
                biz_opaque_callback_data=biz_opaque_callback_data,
            )
        )

    def pre_accept(self, *, call_id: str, sdp_answer: str) -> dict:
        """Pre-establish media before accepting an inbound call.

        Args:
            call_id: WhatsApp call ID.
            sdp_answer: RFC 8866 SDP answer.

        Returns:
            Meta response body.
        """
        return self.act(
            CallAction(
                action="pre_accept",
                call_id=call_id,
                session=CallSession(sdp_type="answer", sdp=sdp_answer),
            )
        )

    def accept(self, *, call_id: str, sdp_answer: str) -> dict:
        """Accept an inbound call.

        Args:
            call_id: WhatsApp call ID.
            sdp_answer: RFC 8866 SDP answer.

        Returns:
            Meta response body.
        """
        return self.act(
            CallAction(
                action="accept",
                call_id=call_id,
                session=CallSession(sdp_type="answer", sdp=sdp_answer),
            )
        )

    def reject(self, *, call_id: str) -> dict:
        """Reject an inbound call.

        Args:
            call_id: WhatsApp call ID.

        Returns:
            Meta response body.
        """
        return self.act(CallAction(action="reject", call_id=call_id))

    def terminate(self, *, call_id: str) -> dict:
        """Terminate an active call.

        Args:
            call_id: WhatsApp call ID.

        Returns:
            Meta response body.
        """
        return self.act(CallAction(action="terminate", call_id=call_id))

    def get_permission(self, user_wa_id: str) -> CallPermission:
        """Read call permission state for a user.

        Args:
            user_wa_id: WhatsApp user identifier.

        Returns:
            Permission state.
        """
        response = self.transport.send(
            Request(
                method="GET",
                path=f"/{self.phone_number_id}/call_permissions",
                params={"user_wa_id": user_wa_id},
            )
        )
        return CallPermission(**response.data)

    def get_settings(self) -> CallSettings:
        """Read calling configuration for the business number.

        Returns:
            Call settings.
        """
        response = self.transport.send(
            Request(method="GET", path=f"/{self.phone_number_id}/settings")
        )
        return CallSettings(**response.data)


class AsyncCallService:
    """Asynchronous voice call operations sharing sync contracts.

    Attributes:
        transport: Shared pooled async transport.
        phone_number_id: Sender phone number ID.
    """

    def __init__(self, transport: AsyncTransport, phone_number_id: str) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled async transport.
            phone_number_id: Sender phone number ID.
        """
        self.transport = transport
        self.phone_number_id = phone_number_id

    async def act(self, action: CallAction) -> dict:
        """Execute a call action.

        Args:
            action: Validated call action.

        Returns:
            Meta response body.
        """
        response = await self.transport.asend(
            Request(
                method="POST",
                path=f"/{self.phone_number_id}/calls",
                json_body=action.payload(),
            )
        )
        return response.data

    async def terminate(self, *, call_id: str) -> dict:
        """Terminate an active call.

        Args:
            call_id: WhatsApp call ID.

        Returns:
            Meta response body.
        """
        return await self.act(CallAction(action="terminate", call_id=call_id))


__all__ = ["AsyncCallService", "CallService"]
