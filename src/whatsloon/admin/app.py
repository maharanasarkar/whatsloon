"""Admin FastAPI application factory (``whatsloon[admin]`` extra)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Query
    from fastapi.responses import JSONResponse
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Admin console requires the 'admin' extra: pip install 'whatsloon[admin]'."
    ) from exc

from whatsloon.admin import views
from whatsloon.admin.auth import AdminAuth, AdminUser
from whatsloon.persistence.base import EventFilter, MessageFilter


@dataclass
class RepositoryBundle:
    """Repository set exposed to admin views.

    Attributes:
        conversations: Conversation store.
        messages: Message store.
        events: Webhook event store.
    """

    conversations: Any
    messages: Any
    events: Any


def create_app(
    store: RepositoryBundle, auth: AdminAuth, processor: Optional[Any] = None
) -> FastAPI:
    """Create the admin FastAPI application.

    Args:
        store: Repository bundle for read views.
        auth: Pluggable authentication backend.
        processor: Optional webhook processor enabling event retries.

    Returns:
        Configured FastAPI application.

    Raises:
        RuntimeError: If no authentication backend is configured.
    """
    if auth is None:
        raise RuntimeError("Admin console requires an AdminAuth backend; refusing no-auth mode.")
    app = FastAPI(title="whatsloon admin", version="3")

    try:
        from whatsloon.admin.ui import create_ui_router

        app.include_router(create_ui_router(store, auth, processor=processor))
    except ImportError:
        # jinja2 missing: HTML pages skipped, JSON API still served.
        pass

    def current_user(authorization: Optional[str] = Header(default=None)) -> AdminUser:
        """Resolve the bearer token to a principal.

        Args:
            authorization: Authorization header value.

        Returns:
            Authenticated principal.

        Raises:
            HTTPException: When the token is missing or invalid.
        """
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
        user = auth.authenticate(token)
        if user is None:
            raise HTTPException(status_code=401, detail="unauthorized")
        return user

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report liveness without authentication.

        Returns:
            Liveness mapping.
        """
        return {"status": "ok"}

    @app.get("/dashboard")
    def get_dashboard(tenant_id: str, user: AdminUser = Depends(current_user)) -> JSONResponse:
        """Return operational counts for a tenant.

        Args:
            tenant_id: Tenant scope.
            user: Authenticated principal.

        Returns:
            Dashboard mapping or error status.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return JSONResponse(denied, status_code=denied["status"])
        return JSONResponse(views.dashboard(store, tenant_id))

    @app.get("/conversations")
    def list_conversations(
        tenant_id: str, limit: int = 50, user: AdminUser = Depends(current_user)
    ) -> JSONResponse:
        """List conversations with masked participants.

        Args:
            tenant_id: Tenant scope.
            limit: Maximum rows.
            user: Authenticated principal.

        Returns:
            Conversation list or error status.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return JSONResponse(denied, status_code=denied["status"])
        items = [
            {
                "id": c.id,
                "participant": views.mask_phone(c.participant),
                "last_activity_at": c.last_activity_at.isoformat(),
            }
            for c in store.conversations.list(tenant_id, limit=limit)
        ]
        return JSONResponse({"items": items})

    @app.get("/messages")
    def search_messages(
        tenant_id: str,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        user: AdminUser = Depends(current_user),
    ) -> JSONResponse:
        """Search messages with masking applied.

        Args:
            tenant_id: Tenant scope.
            status: Optional delivery status filter.
            direction: Optional direction filter.
            user: Authenticated principal.

        Returns:
            Message list or error status.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return JSONResponse(denied, status_code=denied["status"])
        query = MessageFilter(tenant_id=tenant_id, status=status, direction=direction)
        items = [views.serialize_message(m) for m in store.messages.search(query)]
        return JSONResponse({"items": items})

    @app.get("/messages/{message_id}")
    def get_message(
        message_id: str,
        tenant_id: str,
        reveal_raw: bool = Query(default=False),
        user: AdminUser = Depends(current_user),
    ) -> JSONResponse:
        """Fetch a message; raw payload needs a privileged role.

        Args:
            message_id: Local identifier.
            tenant_id: Tenant scope.
            reveal_raw: Whether to include the redacted structured payload.
            user: Authenticated principal.

        Returns:
            Message detail or error status.
        """
        body, status = views.message_detail(
            store, user, tenant_id, message_id, reveal_raw=reveal_raw
        )
        return JSONResponse(body, status_code=status)

    @app.get("/events")
    def list_events(
        tenant_id: str,
        processing_status: Optional[str] = None,
        user: AdminUser = Depends(current_user),
    ) -> JSONResponse:
        """List webhook events with failure visibility.

        Args:
            tenant_id: Tenant scope.
            processing_status: Optional processing state filter.
            user: Authenticated principal.

        Returns:
            Event list or error status.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return JSONResponse(denied, status_code=denied["status"])
        query = EventFilter(tenant_id=tenant_id, processing_status=processing_status)
        items = [
            {
                "id": e.id,
                "event_type": e.event_type,
                "processing_status": e.processing_status.value,
                "retry_count": e.retry_count,
                "received_at": e.received_at.isoformat(),
            }
            for e in store.events.search(query)
        ]
        return JSONResponse({"items": items})

    @app.post("/events/{event_id}/retry")
    def retry_event(
        event_id: str,
        tenant_id: str,
        user: AdminUser = Depends(current_user),
    ) -> JSONResponse:
        """Re-dispatch a stored event from its retained raw payload.

        Args:
            event_id: Stored event identifier.
            tenant_id: Tenant scope.
            user: Authenticated principal.

        Returns:
            Retry outcome, 404 for unknown IDs, or 501 without a processor.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return JSONResponse(denied, status_code=denied["status"])
        if processor is None:
            return JSONResponse({"error": "retry unavailable: no processor wired"}, status_code=501)
        result = processor.retry_event(tenant_id, event_id)
        status = 404 if result.outcome == "missing" else 200
        return JSONResponse(
            {
                "event_id": result.event_id,
                "event_type": result.event_type,
                "outcome": result.outcome,
                "detail": result.detail,
            },
            status_code=status,
        )

    return app


__all__ = ["RepositoryBundle", "create_app"]
