"""Template management services (WhatsApp Manager API)."""

from __future__ import annotations

from whatsloon.templates.models import TemplateInfo, TemplateSpec
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport


class TemplateService:
    """Synchronous template operations scoped per WABA.

    Attributes:
        transport: Shared pooled transport.
    """

    def __init__(self, transport: SyncTransport) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled transport.
        """
        self.transport = transport

    def list_templates(self, waba_id: str) -> list[TemplateInfo]:
        """List templates for a WhatsApp Business Account.

        Args:
            waba_id: WhatsApp Business Account ID.

        Returns:
            Template summaries.
        """
        response = self.transport.send(Request(method="GET", path=f"/{waba_id}/message_templates"))
        return [TemplateInfo(**item) for item in response.data.get("data", [])]

    def create_template(self, waba_id: str, spec: TemplateSpec) -> TemplateInfo:
        """Create a template for approval.

        Args:
            waba_id: WhatsApp Business Account ID.
            spec: Creation specification.

        Returns:
            Created template summary.
        """
        response = self.transport.send(
            Request(method="POST", path=f"/{waba_id}/message_templates", json_body=spec.payload())
        )
        info = {"name": spec.name, "language": spec.language, "category": spec.category}
        info.update(response.data)
        return TemplateInfo(**info)

    def delete_template(self, waba_id: str, name: str) -> bool:
        """Delete a template by name.

        Args:
            waba_id: WhatsApp Business Account ID.
            name: Template name.

        Returns:
            True when Meta confirms deletion.
        """
        response = self.transport.send(
            Request(
                method="DELETE",
                path=f"/{waba_id}/message_templates",
                params={"name": name},
            )
        )
        return bool(response.data.get("success", response.status_code == 200))


class AsyncTemplateService:
    """Asynchronous template operations scoped per WABA.

    Attributes:
        transport: Shared pooled async transport.
    """

    def __init__(self, transport: AsyncTransport) -> None:
        """Initialize the service.

        Args:
            transport: Shared pooled async transport.
        """
        self.transport = transport

    async def list_templates(self, waba_id: str) -> list[TemplateInfo]:
        """List templates for a WhatsApp Business Account.

        Args:
            waba_id: WhatsApp Business Account ID.

        Returns:
            Template summaries.
        """
        response = await self.transport.asend(
            Request(method="GET", path=f"/{waba_id}/message_templates")
        )
        return [TemplateInfo(**item) for item in response.data.get("data", [])]

    async def delete_template(self, waba_id: str, name: str) -> bool:
        """Delete a template by name.

        Args:
            waba_id: WhatsApp Business Account ID.
            name: Template name.

        Returns:
            True when Meta confirms deletion.
        """
        response = await self.transport.asend(
            Request(
                method="DELETE",
                path=f"/{waba_id}/message_templates",
                params={"name": name},
            )
        )
        return bool(response.data.get("success", response.status_code == 200))


__all__ = ["AsyncTemplateService", "TemplateService"]
