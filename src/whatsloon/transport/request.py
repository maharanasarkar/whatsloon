"""Outbound transport request model."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class Request(BaseModel):
    """An outbound Graph API request.

    Attributes:
        method: HTTP method.
        path: URL path beginning with ``/``, or an absolute URL for
            out-of-band resources such as media download URLs.
        params: Query parameters.
        json_body: JSON payload, if any. Mutually exclusive with files.
        files: Multipart upload mapping of field name to
            ``(filename, content, mime_type)`` tuples.
        form_data: Multipart form fields sent alongside files.
        headers: Extra headers merged over auth headers.
        timeout_override: Per-operation read timeout in seconds.
        idempotency_key: Stable key for safe retries.
        correlation_id: SDK-generated or caller-supplied correlation ID.
    """

    model_config = {"arbitrary_types_allowed": True}

    method: str = "POST"
    path: str
    params: dict[str, Any] = Field(default_factory=dict)
    json_body: Optional[dict[str, Any]] = None
    files: Optional[dict[str, Any]] = None
    form_data: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_override: Optional[float] = None
    idempotency_key: str = Field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
