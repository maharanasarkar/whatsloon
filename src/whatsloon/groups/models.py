"""Group management models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Group(BaseModel):
    """WhatsApp group summary.

    Attributes:
        id: Group identifier used as the message ``to``.
        subject: Group name.
        description: Group description.
        invite_link: Shareable invite link when reported.
        participant_count: Participant count when reported.
    """

    model_config = {"extra": "allow"}

    id: str = ""
    subject: str = ""
    description: Optional[str] = None
    invite_link: Optional[str] = None
    participant_count: Optional[int] = None


class GroupCreate(BaseModel):
    """Group creation specification.

    Attributes:
        subject: Group name.
        description: Optional group description.
        join_approval_mode: Either ``auto_approve`` or ``approval_required``.
    """

    subject: str = Field(min_length=1)
    description: Optional[str] = None
    join_approval_mode: str = "auto_approve"

    def payload(self) -> dict[str, object]:
        """Render the Meta creation payload.

        Returns:
            Creation payload.
        """
        body: dict[str, object] = {
            "messaging_product": "whatsapp",
            "subject": self.subject,
            "join_approval_mode": self.join_approval_mode,
        }
        if self.description:
            body["description"] = self.description
        return body


class JoinRequest(BaseModel):
    """Pending group join request.

    Attributes:
        id: Request identifier.
        wa_id: Requesting user identifier.
        requested_at: Request timestamp when reported.
    """

    model_config = {"extra": "allow"}

    id: str = ""
    wa_id: str = ""
    requested_at: Optional[str] = None
