"""Voice call models for the Calling API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CallSession(BaseModel):
    """WebRTC session description.

    Attributes:
        sdp_type: Either ``"offer"`` (connect) or ``"answer"`` (accept).
        sdp: RFC 8866 SDP string.
    """

    sdp_type: str = Field(pattern="^(offer|answer)$")
    sdp: str = Field(min_length=1)


class CallAction(BaseModel):
    """Call action request.

    Attributes:
        action: One of connect, pre_accept, accept, reject, terminate.
        to: Callee for business-initiated connects.
        call_id: Call identifier for pre_accept/accept/reject/terminate.
        session: SDP session for connect/pre_accept/accept.
        biz_opaque_callback_data: Tracking string echoed in webhooks.
    """

    action: str = Field(pattern="^(connect|pre_accept|accept|reject|terminate)$")
    to: Optional[str] = None
    call_id: Optional[str] = None
    session: Optional[CallSession] = None
    biz_opaque_callback_data: Optional[str] = Field(default=None, max_length=512)

    def payload(self) -> dict[str, Any]:
        """Render the Meta action payload.

        Returns:
            Action payload.
        """
        body: dict[str, Any] = {"messaging_product": "whatsapp", "action": self.action}
        if self.to:
            body["to"] = self.to
        if self.call_id:
            body["call_id"] = self.call_id
        if self.session is not None:
            body["session"] = self.session.model_dump()
        if self.biz_opaque_callback_data:
            body["biz_opaque_callback_data"] = self.biz_opaque_callback_data
        return body


class CallPermission(BaseModel):
    """Call permission state for a user.

    Attributes:
        status: Permission status when reported.
        expiration_timestamp: Expiry when reported.
    """

    model_config = {"extra": "allow"}

    status: str = ""
    expiration_timestamp: Optional[str] = None


class CallSettings(BaseModel):
    """Calling configuration for a business number.

    Attributes:
        status: Calling status when reported.
    """

    model_config = {"extra": "allow"}

    status: str = ""
