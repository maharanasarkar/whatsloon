"""Group management services.

Groups are invite-only: the API creates groups and removes participants,
but new members join via invite links (there is no add-participant
endpoint). Group messaging reuses the messages endpoint with
``recipient_type`` set to ``group``.
"""

from __future__ import annotations

from typing import Optional

from whatsloon.groups.models import Group, GroupCreate, JoinRequest
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport


class GroupService:
    """Synchronous group operations.

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

    def create_group(self, spec: GroupCreate) -> Group:
        """Create a group and return its invite link.

        Args:
            spec: Creation specification.

        Returns:
            Created group summary.
        """
        response = self.transport.send(
            Request(
                method="POST",
                path=f"/{self.phone_number_id}/groups",
                json_body=spec.payload(),
            )
        )
        return Group(**response.data)

    def list_groups(self) -> list[Group]:
        """List groups for the business number.

        Returns:
            Group summaries.
        """
        response = self.transport.send(
            Request(method="GET", path=f"/{self.phone_number_id}/groups")
        )
        return [Group(**item) for item in response.data.get("data", [])]

    def get_group(self, group_id: str) -> Group:
        """Fetch one group summary.

        Args:
            group_id: Group identifier.

        Returns:
            Group summary.
        """
        response = self.transport.send(Request(method="GET", path=f"/{group_id}"))
        return Group(**response.data)

    def update_group(
        self, group_id: str, *, subject: Optional[str] = None, description: Optional[str] = None
    ) -> Group:
        """Update group metadata.

        Args:
            group_id: Group identifier.
            subject: New group name.
            description: New group description.

        Returns:
            Updated group summary.
        """
        body: dict[str, object] = {"messaging_product": "whatsapp"}
        if subject is not None:
            body["subject"] = subject
        if description is not None:
            body["description"] = description
        response = self.transport.send(Request(method="POST", path=f"/{group_id}", json_body=body))
        return Group(**response.data)

    def delete_group(self, group_id: str) -> bool:
        """Delete a group.

        Args:
            group_id: Group identifier.

        Returns:
            True when Meta confirms deletion.
        """
        response = self.transport.send(Request(method="DELETE", path=f"/{group_id}"))
        return bool(response.data.get("success", response.status_code == 200))

    def list_join_requests(self, group_id: str) -> list[JoinRequest]:
        """List pending join requests for a group.

        Args:
            group_id: Group identifier.

        Returns:
            Pending requests.
        """
        response = self.transport.send(Request(method="GET", path=f"/{group_id}/join_requests"))
        return [JoinRequest(**item) for item in response.data.get("data", [])]

    def approve_join_request(self, group_id: str, request_id: str) -> bool:
        """Approve a pending join request.

        Args:
            group_id: Group identifier.
            request_id: Join request identifier.

        Returns:
            True when Meta confirms approval.
        """
        response = self.transport.send(
            Request(method="POST", path=f"/{group_id}/join_requests/{request_id}/approve")
        )
        return bool(response.data.get("success", response.status_code == 200))

    def reject_join_request(self, group_id: str, request_id: str) -> bool:
        """Reject a pending join request.

        Args:
            group_id: Group identifier.
            request_id: Join request identifier.

        Returns:
            True when Meta confirms rejection.
        """
        response = self.transport.send(
            Request(method="POST", path=f"/{group_id}/join_requests/{request_id}/reject")
        )
        return bool(response.data.get("success", response.status_code == 200))

    def remove_participants(self, group_id: str, wa_ids: list[str]) -> bool:
        """Remove participants from a group.

        Args:
            group_id: Group identifier.
            wa_ids: Participant identifiers to remove.

        Returns:
            True when Meta confirms removal.
        """
        response = self.transport.send(
            Request(
                method="DELETE",
                path=f"/{group_id}/participants",
                json_body={"wa_ids": wa_ids},
            )
        )
        return bool(response.data.get("success", response.status_code == 200))


class AsyncGroupService:
    """Asynchronous group operations sharing sync contracts.

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

    async def create_group(self, spec: GroupCreate) -> Group:
        """Create a group and return its invite link.

        Args:
            spec: Creation specification.

        Returns:
            Created group summary.
        """
        response = await self.transport.asend(
            Request(
                method="POST",
                path=f"/{self.phone_number_id}/groups",
                json_body=spec.payload(),
            )
        )
        return Group(**response.data)

    async def list_groups(self) -> list[Group]:
        """List groups for the business number.

        Returns:
            Group summaries.
        """
        response = await self.transport.asend(
            Request(method="GET", path=f"/{self.phone_number_id}/groups")
        )
        return [Group(**item) for item in response.data.get("data", [])]

    async def remove_participants(self, group_id: str, wa_ids: list[str]) -> bool:
        """Remove participants from a group.

        Args:
            group_id: Group identifier.
            wa_ids: Participant identifiers to remove.

        Returns:
            True when Meta confirms removal.
        """
        response = await self.transport.asend(
            Request(
                method="DELETE",
                path=f"/{group_id}/participants",
                json_body={"wa_ids": wa_ids},
            )
        )
        return bool(response.data.get("success", response.status_code == 200))


__all__ = ["AsyncGroupService", "GroupService"]
