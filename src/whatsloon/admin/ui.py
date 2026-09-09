"""Server-rendered admin pages (Jinja2 + HTMX, no JS build step).

The JSON API is untouched; these routes render the same masked view data
as HTML. Browsers cannot send Authorization headers from links, so pages
also accept a ``token`` query parameter as an explicit, documented fallback
for this reference console. Prefer header auth for non-browser clients.
"""

from __future__ import annotations

from importlib import resources
from typing import Any, Optional

try:
    from fastapi import APIRouter, Depends, Header, Query, Request
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Admin console requires the 'admin' extra: pip install 'whatsloon[admin]'."
    ) from exc

from whatsloon.admin import views
from whatsloon.admin.auth import AdminAuth, AdminUser
from whatsloon.persistence.base import EventFilter, MessageFilter


def _template_dir() -> str:
    """Locate the bundled template directory.

    Returns:
        Filesystem path to Jinja2 templates.
    """
    return str(resources.files("whatsloon.admin") / "templates")


def resolve_user(
    auth: AdminAuth,
    authorization: Optional[str] = None,
    token: Optional[str] = None,
) -> Optional[AdminUser]:
    """Resolve a principal from header or query token.

    Args:
        auth: Authentication backend.
        authorization: Authorization header value.
        token: Query-string token fallback for browser navigation.

    Returns:
        Principal or None when unauthorized.
    """
    candidate = token
    if authorization and authorization.lower().startswith("bearer "):
        candidate = authorization[7:]
    return auth.authenticate(candidate)


def error_page(
    templates: Jinja2Templates,
    request: Request,
    *,
    status: int,
    heading: str,
    message: str,
    tenant_id: str = "",
    token: str = "",
) -> HTMLResponse:
    """Render an error page.

    Args:
        templates: Jinja2 environment.
        request: Incoming request.
        status: HTTP status.
        heading: Short title.
        message: Human-readable explanation.
        tenant_id: Tenant scope for navigation.
        token: Token for navigation links.

    Returns:
        HTML error response.
    """
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "root": request.scope.get("root_path", ""),
            "status": status,
            "heading": heading,
            "message": message,
            "tenant_id": tenant_id,
            "token": token or "",
            "user": "",
            "active": "",
        },
        status_code=status,
    )


def _parse_date(value: Optional[str]) -> Optional[Any]:
    """Parse a YYYY-MM-DD query date, ignoring invalid input.

    Args:
        value: Candidate date string.

    Returns:
        Midnight UTC datetime or None.
    """
    from datetime import datetime, timezone

    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _page_window(offset: int, limit: int, count: int) -> dict[str, Any]:
    """Build prev/next pagination context.

    Args:
        offset: Current offset.
        limit: Page size.
        count: Rows on this page.

    Returns:
        Pagination mapping.
    """
    return {
        "offset": offset,
        "limit": limit,
        "has_prev": offset > 0,
        "has_more": count >= limit,
        "prev_offset": max(0, offset - limit),
        "next_offset": offset + limit,
    }


def base_context(
    request: Request, user: AdminUser, tenant_id: str, token: Optional[str], active: str
) -> dict[str, Any]:
    """Build shared template context.

    Args:
        request: Incoming request.
        user: Authenticated principal.
        tenant_id: Tenant scope.
        token: Query token for navigation links.
        active: Active nav item.

    Returns:
        Template context mapping.
    """
    return {
        "root": request.scope.get("root_path", ""),
        "tenant_id": tenant_id,
        "token": token or "",
        "user": user.username,
        "active": active,
    }


def create_ui_router(store: Any, auth: AdminAuth, processor: Optional[Any] = None) -> APIRouter:
    """Create HTML page and HTMX partial routes.

    Args:
        store: Repository bundle for read views.
        auth: Pluggable authentication backend.
        processor: Optional webhook processor enabling event retries.

    Returns:
        Configured router to include on the admin app.
    """
    templates = Jinja2Templates(directory=_template_dir())
    router = APIRouter()

    @router.get("/ui/static/admin.css")
    def admin_css() -> Any:
        """Serve the bundled admin stylesheet (no build step).

        Returns:
            CSS file response honoring the mount prefix.
        """
        from fastapi.responses import FileResponse

        return FileResponse(
            str(resources.files("whatsloon.admin") / "static" / "admin.css"),
            media_type="text/css",
        )

    def principal(
        authorization: Optional[str] = Header(default=None),
        token: Optional[str] = Query(default=None),
    ) -> AdminUser:
        """Resolve the request principal or raise 401.

        Args:
            authorization: Authorization header value.
            token: Query-string token fallback.

        Returns:
            Authenticated principal.

        Raises:
            HTTPException: When unauthorized (rendered as an HTML page).
        """
        from fastapi import HTTPException

        user = resolve_user(auth, authorization, token)
        if user is None:
            raise HTTPException(status_code=401, detail="unauthorized")
        return user

    @router.get("/ui/dashboard", response_class=HTMLResponse)
    def dashboard_page(
        request: Request,
        tenant_id: str,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render the dashboard page.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Dashboard HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden" if denied["status"] == 403 else "Unauthorized",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        context = base_context(request, user, tenant_id, token, "dashboard")
        context["stats"] = views.dashboard(store, tenant_id)
        return templates.TemplateResponse(request, "dashboard.html", context)

    @router.get("/ui/conversations", response_class=HTMLResponse)
    def conversations_page(
        request: Request,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render the conversations page.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            limit: Maximum rows.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Conversations HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden" if denied["status"] == 403 else "Unauthorized",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        items = [
            {
                "id": c.id,
                "participant": views.mask_phone(c.participant),
                "last_activity_at": c.last_activity_at.isoformat(),
            }
            for c in store.conversations.list(tenant_id, limit=limit, offset=offset)
        ]
        context = base_context(request, user, tenant_id, token, "conversations")
        context.update({"items": items, "limit": limit})
        context.update(_page_window(offset, limit, len(items)))
        return templates.TemplateResponse(request, "conversations.html", context)

    @router.get("/ui/conversations/{conversation_id}", response_class=HTMLResponse)
    def conversation_thread_page(
        request: Request,
        conversation_id: str,
        tenant_id: str,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render one conversation thread in chronological order.

        Args:
            request: Incoming request.
            conversation_id: Local identifier.
            tenant_id: Tenant scope.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Thread HTML or an error page.
        """
        body, status = views.conversation_detail(store, user, tenant_id, conversation_id)
        if status != 200 or body is None:
            return error_page(
                templates,
                request,
                status=status,
                heading="Not found" if status == 404 else "Forbidden",
                message="The conversation does not exist or cannot be viewed.",
                tenant_id=tenant_id,
                token=token or "",
            )
        context = base_context(request, user, tenant_id, token, "conversations")
        context.update({"thread": body})
        return templates.TemplateResponse(request, "conversation.html", context)

    @router.get("/ui/partials/conversations", response_class=HTMLResponse)
    def conversations_partial(
        request: Request,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render conversation rows for HTMX swaps.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            limit: Maximum rows.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Table-row fragment.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return HTMLResponse("<tr><td>Forbidden</td></tr>", status_code=denied["status"])
        items = [
            {
                "id": c.id,
                "participant": views.mask_phone(c.participant),
                "last_activity_at": c.last_activity_at.isoformat(),
            }
            for c in store.conversations.list(tenant_id, limit=limit, offset=offset)
        ]
        context = base_context(request, user, tenant_id, token, "conversations")
        context.update({"items": items, "limit": limit})
        return templates.TemplateResponse(request, "_conversation_rows.html", context)

    @router.get("/ui/messages", response_class=HTMLResponse)
    def messages_page(
        request: Request,
        tenant_id: str,
        status: Optional[str] = Query(default=None),
        direction: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None),
        since: Optional[str] = Query(default=None),
        until: Optional[str] = Query(default=None),
        limit: int = 50,
        offset: int = 0,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render the messages page.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            status: Optional delivery status filter.
            direction: Optional direction filter.
            q: Optional content substring search.
            since: Optional start date (YYYY-MM-DD).
            until: Optional end date (YYYY-MM-DD).
            limit: Page size.
            offset: Page offset.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Messages HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden" if denied["status"] == 403 else "Unauthorized",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        query = MessageFilter(
            tenant_id=tenant_id,
            status=status,
            direction=direction,
            content_contains=q or None,
            since=_parse_date(since),
            until=_parse_date(until),
            limit=limit,
            offset=offset,
        )
        items = [views.serialize_message(m) for m in store.messages.search(query)]
        context = base_context(request, user, tenant_id, token, "messages")
        context.update(
            {
                "items": items,
                "status": status or "",
                "direction": direction or "",
                "q": q or "",
                "since": since or "",
                "until": until or "",
            }
        )
        context.update(_page_window(offset, limit, len(items)))
        return templates.TemplateResponse(request, "messages.html", context)

    @router.get("/ui/partials/messages", response_class=HTMLResponse)
    def messages_partial(
        request: Request,
        tenant_id: str,
        status: Optional[str] = Query(default=None),
        direction: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None),
        since: Optional[str] = Query(default=None),
        until: Optional[str] = Query(default=None),
        limit: int = 50,
        offset: int = 0,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render message rows for HTMX swaps.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            status: Optional delivery status filter.
            direction: Optional direction filter.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Table-row fragment.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return HTMLResponse("<tr><td>Forbidden</td></tr>", status_code=denied["status"])
        query = MessageFilter(
            tenant_id=tenant_id,
            status=status,
            direction=direction,
            content_contains=q or None,
            since=_parse_date(since),
            until=_parse_date(until),
            limit=limit,
            offset=offset,
        )
        context = base_context(request, user, tenant_id, token, "messages")
        context.update(
            {
                "items": [views.serialize_message(m) for m in store.messages.search(query)],
                "status": status or "",
                "direction": direction or "",
                "q": q or "",
                "since": since or "",
                "until": until or "",
            }
        )
        return templates.TemplateResponse(request, "_message_rows.html", context)

    @router.get("/ui/messages/{message_id}", response_class=HTMLResponse)
    def message_detail_page(
        request: Request,
        message_id: str,
        tenant_id: str,
        reveal_raw: bool = Query(default=False),
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render one message with status history.

        Args:
            request: Incoming request.
            message_id: Local identifier.
            tenant_id: Tenant scope.
            reveal_raw: Whether to include the redacted structured payload.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Detail HTML or an error page.
        """
        body, status = views.message_detail(
            store, user, tenant_id, message_id, reveal_raw=reveal_raw
        )
        if status != 200:
            return error_page(
                templates,
                request,
                status=status,
                heading="Not found" if status == 404 else "Forbidden",
                message="The message does not exist or cannot be viewed.",
                tenant_id=tenant_id,
                token=token or "",
            )
        context = base_context(request, user, tenant_id, token, "messages")
        context.update(
            {
                "detail": body,
                "reveal": reveal_raw and user.can_view_raw,
                "can_view_raw": user.can_view_raw,
            }
        )
        return templates.TemplateResponse(request, "message_detail.html", context)

    @router.get("/ui/events", response_class=HTMLResponse)
    def events_page(
        request: Request,
        tenant_id: str,
        processing_status: Optional[str] = Query(default=None),
        since: Optional[str] = Query(default=None),
        until: Optional[str] = Query(default=None),
        limit: int = 50,
        offset: int = 0,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render the events page.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            processing_status: Optional processing state filter.
            since: Optional start date (YYYY-MM-DD).
            until: Optional end date (YYYY-MM-DD).
            limit: Page size.
            offset: Page offset.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Events HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden" if denied["status"] == 403 else "Unauthorized",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        query = EventFilter(
            tenant_id=tenant_id,
            processing_status=processing_status,
            since=_parse_date(since),
            until=_parse_date(until),
            limit=limit,
            offset=offset,
        )
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
        context = base_context(request, user, tenant_id, token, "events")
        context.update(
            {
                "items": items,
                "processing_status": processing_status or "",
                "since": since or "",
                "until": until or "",
                "can_retry": processor is not None,
            }
        )
        context.update(_page_window(offset, limit, len(items)))
        return templates.TemplateResponse(request, "events.html", context)

    @router.get("/ui/partials/events", response_class=HTMLResponse)
    def events_partial(
        request: Request,
        tenant_id: str,
        processing_status: Optional[str] = Query(default=None),
        since: Optional[str] = Query(default=None),
        until: Optional[str] = Query(default=None),
        limit: int = 50,
        offset: int = 0,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render event rows for HTMX swaps.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            processing_status: Optional processing state filter.
            since: Optional start date (YYYY-MM-DD).
            until: Optional end date (YYYY-MM-DD).
            limit: Page size.
            offset: Page offset.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Table-row fragment.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return HTMLResponse("<tr><td>Forbidden</td></tr>", status_code=denied["status"])
        query = EventFilter(
            tenant_id=tenant_id,
            processing_status=processing_status,
            since=_parse_date(since),
            until=_parse_date(until),
            limit=limit,
            offset=offset,
        )
        context = base_context(request, user, tenant_id, token, "events")
        context.update(
            {
                "items": [
                    {
                        "id": e.id,
                        "event_type": e.event_type,
                        "processing_status": e.processing_status.value,
                        "retry_count": e.retry_count,
                        "received_at": e.received_at.isoformat(),
                    }
                    for e in store.events.search(query)
                ],
                "processing_status": processing_status or "",
                "since": since or "",
                "until": until or "",
                "can_retry": processor is not None,
            }
        )
        return templates.TemplateResponse(request, "_event_rows.html", context)

    @router.post("/ui/events/{event_id}/retry", response_class=HTMLResponse)
    def retry_event_row(
        request: Request,
        event_id: str,
        tenant_id: str,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Retry one event and re-render its row.

        Args:
            request: Incoming request.
            event_id: Stored event identifier.
            tenant_id: Tenant scope.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Updated row fragment.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return HTMLResponse("<tr><td>Forbidden</td></tr>", status_code=denied["status"])
        if processor is None:
            return HTMLResponse("<tr><td>Retry unavailable</td></tr>", status_code=501)
        result = processor.retry_event(tenant_id, event_id)
        if result.outcome == "missing":
            return HTMLResponse("<tr><td>Not found</td></tr>", status_code=404)
        record = store.events.get(tenant_id, event_id)
        context = base_context(request, user, tenant_id, token, "events")
        context.update(
            {
                "items": [
                    {
                        "id": record.id,
                        "event_type": record.event_type,
                        "processing_status": record.processing_status.value,
                        "retry_count": record.retry_count,
                        "received_at": record.received_at.isoformat(),
                    }
                ],
                "can_retry": True,
            }
        )
        return templates.TemplateResponse(request, "_event_rows.html", context)

    return router


__all__ = ["base_context", "create_ui_router", "error_page", "resolve_user"]
