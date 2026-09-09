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


SESSION_COOKIE = "wa_session"
"""Session cookie name for browser logins."""

SESSION_TTL_SECONDS = 12 * 60 * 60
"""Browser session lifetime."""


class SessionStore:
    """In-memory browser sessions for the reference console.

    Production deployments should replace this with persistent storage
    plus CSRF protection; the SameSite cookie here only raises the bar
    for cross-site forgery, it does not eliminate it.
    """

    def __init__(self) -> None:
        """Initialize empty session storage."""
        from datetime import timedelta

        self._sessions: dict[str, tuple[AdminUser, Any]] = {}
        self._ttl = timedelta(seconds=SESSION_TTL_SECONDS)

    def create(self, user: AdminUser) -> str:
        """Create a session for a principal.

        Args:
            user: Authenticated principal.

        Returns:
            Opaque session token for the cookie value.
        """
        import secrets
        from datetime import datetime, timezone

        token = secrets.token_urlsafe(32)
        self._sessions[token] = (user, datetime.now(timezone.utc) + self._ttl)
        return token

    def lookup(self, token: Optional[str]) -> Optional[AdminUser]:
        """Resolve a session token, expiring stale entries.

        Args:
            token: Cookie value.

        Returns:
            Principal or None.
        """
        from datetime import datetime, timezone

        if not token:
            return None
        entry = self._sessions.get(token)
        if entry is None:
            return None
        user, expires = entry
        if datetime.now(timezone.utc) > expires:
            del self._sessions[token]
            return None
        return user

    def destroy(self, token: Optional[str]) -> None:
        """Drop a session.

        Args:
            token: Cookie value.
        """
        if token:
            self._sessions.pop(token, None)


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
    request: Request,
    user: AdminUser,
    tenant_id: str,
    token: Optional[str],
    active: str,
    *,
    wa: Optional[Any] = None,
) -> dict[str, Any]:
    """Build shared template context.

    Args:
        request: Incoming request.
        user: Authenticated principal.
        tenant_id: Tenant scope.
        token: Query token for navigation links.
        active: Active nav item.
        wa: Optional v3 client toggling manager navigation.

    Returns:
        Template context mapping.
    """
    return {
        "root": request.scope.get("root_path", ""),
        "tenant_id": tenant_id,
        "token": token or "",
        "user": user.username,
        "active": active,
        "via_session": bool(request.cookies.get(SESSION_COOKIE)),
        "can_manage": wa is not None,
    }


def create_ui_router(
    store: Any, auth: AdminAuth, processor: Optional[Any] = None, wa: Optional[Any] = None
) -> APIRouter:
    """Create HTML page and HTMX partial routes.

    Args:
        store: Repository bundle for read views.
        auth: Pluggable authentication backend.
        processor: Optional webhook processor enabling event retries.
        wa: Optional v3 client enabling resource managers.

    Returns:
        Configured router to include on the admin app.
    """
    templates = Jinja2Templates(directory=_template_dir())
    router = APIRouter()
    sessions = SessionStore()

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
        request: Request,
        authorization: Optional[str] = Header(default=None),
        token: Optional[str] = Query(default=None),
    ) -> AdminUser:
        """Resolve the request principal or raise 401.

        Checks the session cookie first, then header and query tokens.

        Args:
            request: Incoming request for cookie access.
            authorization: Authorization header value.
            token: Query-string token fallback.

        Returns:
            Authenticated principal.

        Raises:
            HTTPException: When unauthorized (rendered as an HTML page).
        """
        from fastapi import HTTPException

        user = sessions.lookup(request.cookies.get(SESSION_COOKIE))
        if user is None:
            user = resolve_user(auth, authorization, token)
        if user is None:
            raise HTTPException(status_code=401, detail="unauthorized")
        return user

    @router.get("/ui/login", response_class=HTMLResponse)
    def login_page(request: Request) -> HTMLResponse:
        """Render the login form.

        Args:
            request: Incoming request.

        Returns:
            Login HTML.
        """
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "root": request.scope.get("root_path", ""),
                "tenant_id": "",
                "token": "",
                "user": "",
                "active": "",
                "error": "",
            },
        )

    @router.post("/ui/login")
    async def login_submit(request: Request) -> Any:
        """Validate a token and start a browser session.

        Args:
            request: Incoming request with a form-encoded token.

        Returns:
            Redirect to the dashboard with a session cookie, or the
            login page with an error.
        """
        from fastapi.responses import RedirectResponse

        form = await request.form()
        user = auth.authenticate(str(form.get("api_token", "") or "").strip())
        if user is None:
            return templates.TemplateResponse(
                request,
                "login.html",
                {
                    "root": request.scope.get("root_path", ""),
                    "tenant_id": "",
                    "token": "",
                    "user": "",
                    "active": "",
                    "error": "Unknown token.",
                },
                status_code=401,
            )
        response = RedirectResponse(url="./dashboard?tenant_id=", status_code=303)
        response.set_cookie(
            SESSION_COOKIE,
            sessions.create(user),
            max_age=SESSION_TTL_SECONDS,
            httponly=True,
            samesite="lax",
            path="/",
        )
        return response

    @router.post("/ui/logout")
    def logout(request: Request) -> Any:
        """End the browser session.

        Args:
            request: Incoming request.

        Returns:
            Redirect to the login page with the cookie cleared.
        """
        from fastapi.responses import RedirectResponse

        sessions.destroy(request.cookies.get(SESSION_COOKIE))
        response = RedirectResponse(url="./login", status_code=303)
        response.delete_cookie(SESSION_COOKIE, path="/")
        return response

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
        context = base_context(request, user, tenant_id, token, "dashboard", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "conversations", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "conversations", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "conversations", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "messages", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "messages", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "messages", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "events", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "events", wa=wa)
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
        context = base_context(request, user, tenant_id, token, "events", wa=wa)
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

    def _require_wa() -> Any:
        """Return the wired v3 client or raise 501.

        Returns:
            Wired client.

        Raises:
            HTTPException: When no client is wired.
        """
        from fastapi import HTTPException

        if wa is None:
            raise HTTPException(status_code=501, detail="managers unavailable: no client wired")
        return wa

    def _api_error(
        templates: Any, request: Request, exc: Exception, tenant_id: str, token: Optional[str]
    ) -> HTMLResponse:
        """Render a Meta/API failure as an error page.

        Args:
            templates: Jinja2 environment.
            request: Incoming request.
            exc: The failure.
            tenant_id: Tenant scope.
            token: Query token.

        Returns:
            HTML error response.
        """
        return error_page(
            templates,
            request,
            status=502,
            heading="Upstream API error",
            message=f"{type(exc).__name__}: {str(exc)[:300]}",
            tenant_id=tenant_id,
            token=token or "",
        )

    @router.get("/ui/templates", response_class=HTMLResponse)
    def templates_page(
        request: Request,
        tenant_id: str,
        waba_id: str = Query(default=""),
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render template management for a WABA.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            waba_id: WhatsApp Business Account ID.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Templates HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        client = _require_wa()
        items: list[dict[str, Any]] = []
        if waba_id:
            try:
                items = [
                    {"id": t.id, "name": t.name, "status": t.status, "language": t.language}
                    for t in client.templates.list_templates(waba_id)
                ]
            except Exception as exc:
                return _api_error(templates, request, exc, tenant_id, token)
        context = base_context(request, user, tenant_id, token, "templates", wa=wa)
        context.update({"items": items, "waba_id": waba_id})
        return templates.TemplateResponse(request, "templates.html", context)

    @router.post("/ui/templates/create")
    async def templates_create(request: Request) -> Any:
        """Create a template, then redirect to the list.

        Args:
            request: Incoming request with form fields.

        Returns:
            Redirect response.
        """
        from fastapi.responses import RedirectResponse

        from whatsloon.templates.models import TemplateSpec

        form = await request.form()
        tenant_id = str(form.get("tenant_id", ""))
        token = str(form.get("token", "") or "")
        waba_id = str(form.get("waba_id", ""))
        user = resolve_user(auth, None, token or None)
        if user is None or views.check_access(user, tenant_id) is not None:
            return error_page(
                templates,
                request,
                status=403,
                heading="Forbidden",
                message="This principal cannot manage the requested tenant.",
                tenant_id=tenant_id,
                token=token,
            )
        client = _require_wa()
        try:
            client.templates.create_template(
                waba_id,
                TemplateSpec(
                    name=str(form.get("name", "")),
                    language=str(form.get("language", "en_US")),
                    category=str(form.get("category", "UTILITY")),
                ),
            )
        except Exception as exc:
            return _api_error(templates, request, exc, tenant_id, token)
        return RedirectResponse(
            url=f"./templates?tenant_id={tenant_id}&token={token}&waba_id={waba_id}",
            status_code=303,
        )

    @router.get("/ui/media", response_class=HTMLResponse)
    def media_page(
        request: Request,
        tenant_id: str,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render the media upload page.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Media HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        _require_wa()
        context = base_context(request, user, tenant_id, token, "media", wa=wa)
        context.update({"result": None})
        return templates.TemplateResponse(request, "media.html", context)

    @router.post("/ui/media", response_class=HTMLResponse)
    async def media_upload(request: Request) -> HTMLResponse:
        """Upload media and show the resulting ID.

        Args:
            request: Incoming request with a multipart file.

        Returns:
            Result HTML or an error page.
        """
        form = await request.form()
        tenant_id = str(form.get("tenant_id", ""))
        token = str(form.get("token", "") or "")
        user = resolve_user(auth, None, token or None)
        if user is None or views.check_access(user, tenant_id) is not None:
            return error_page(
                templates,
                request,
                status=403,
                heading="Forbidden",
                message="This principal cannot manage the requested tenant.",
                tenant_id=tenant_id,
                token=token,
            )
        client = _require_wa()
        from starlette.datastructures import UploadFile

        upload = form.get("file")
        filename = "upload.bin"
        content = b""
        if isinstance(upload, UploadFile):
            filename = upload.filename or filename
            content = await upload.read()
        mime_type = str(form.get("mime_type", "") or "application/octet-stream")
        context = base_context(request, user, tenant_id, token or None, "media", wa=wa)
        try:
            result = client.media.upload_bytes(content, mime_type, filename=filename)
            context.update({"result": {"media_id": result.media_id, "filename": filename}})
        except Exception as exc:
            return _api_error(templates, request, exc, tenant_id, token)
        return templates.TemplateResponse(request, "media.html", context)

    @router.get("/ui/groups", response_class=HTMLResponse)
    def groups_page(
        request: Request,
        tenant_id: str,
        token: Optional[str] = Query(default=None),
        user: AdminUser = Depends(principal),
    ) -> HTMLResponse:
        """Render group management.

        Args:
            request: Incoming request.
            tenant_id: Tenant scope.
            token: Query token.
            user: Authenticated principal.

        Returns:
            Groups HTML or an error page.
        """
        denied = views.check_access(user, tenant_id)
        if denied is not None:
            return error_page(
                templates,
                request,
                status=denied["status"],
                heading="Forbidden",
                message="This principal cannot view the requested tenant.",
                tenant_id=tenant_id,
                token=token or "",
            )
        client = _require_wa()
        try:
            items = [
                {"id": g.id, "subject": g.subject, "invite_link": g.invite_link or ""}
                for g in client.groups.list_groups()
            ]
        except Exception as exc:
            return _api_error(templates, request, exc, tenant_id, token)
        context = base_context(request, user, tenant_id, token, "groups", wa=wa)
        context.update({"items": items})
        return templates.TemplateResponse(request, "groups.html", context)

    return router


__all__ = ["base_context", "create_ui_router", "error_page", "resolve_user"]
