"""Normalized transport response model."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Response(BaseModel):
    """A normalized Graph API response.

    Attributes:
        status_code: HTTP status code.
        data: Decoded JSON body (empty dict when absent).
        headers: Response headers.
        trace_id: Meta trace/request ID when supplied.
        correlation_id: Echoed request correlation ID.
    """

    model_config = {"arbitrary_types_allowed": True}

    status_code: int
    data: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    correlation_id: str = ""
