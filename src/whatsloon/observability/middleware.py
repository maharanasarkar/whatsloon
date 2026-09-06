"""Transport middleware recording spans and metrics.

Composes with the transport ``TransportMiddleware`` protocol; attach to
services that accept middleware or invoke manually around sends.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any as _Any

from whatsloon.observability.metrics import NoOpMeter
from whatsloon.observability.tracing import NoOpTracer
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response


class ObservabilityMiddleware:
    """Record per-request spans, counters, and latency.

    Attributes:
        tracer: Span factory.
        meter: Metrics recorder.
        clock: Monotonic clock (injectable for tests).
    """

    def __init__(
        self,
        tracer: _Any | None = None,
        meter: _Any | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Initialize the middleware.

        Args:
            tracer: Span factory; defaults to no-op.
            meter: Metrics recorder; defaults to no-op.
            clock: Monotonic clock (injectable for tests).
        """
        self.tracer = tracer or NoOpTracer()
        self.meter = meter or NoOpMeter()
        self._clock = clock
        self._started: dict[str, float] = {}

    def before_send(self, request: Request) -> None:
        """Stamp the start time for a request.

        Args:
            request: Outbound request.
        """
        self._started[request.correlation_id] = self._clock()
        self.meter.increment("whatsloon.requests.started", 1.0, {"path": request.path})

    def after_send(self, request: Request, response: Response) -> None:
        """Record latency and outcome for a completed request.

        Args:
            request: Outbound request.
            response: Normalized response.
        """
        started = self._started.pop(request.correlation_id, None)
        duration = self._clock() - started if started is not None else 0.0
        outcome = "success" if response.status_code < 400 else "error"
        with self.tracer.span(
            "whatsloon.request",
            {"http.method": request.method, "http.status_code": response.status_code},
        ):
            pass
        self.meter.increment(
            "whatsloon.requests.completed",
            1.0,
            {"path": request.path, "status": response.status_code, "outcome": outcome},
        )
        self.meter.observe(
            "whatsloon.requests.duration_seconds",
            duration,
            {"path": request.path, "outcome": outcome},
        )

    def record_error(self, request: Request, error: BaseException) -> None:
        """Record a transport failure without a response.

        Args:
            request: Outbound request.
            error: The failure.
        """
        self._started.pop(request.correlation_id, None)
        with self.tracer.span("whatsloon.request", {"error": type(error).__name__}) as span:
            span.record_exception(error)
        self.meter.increment(
            "whatsloon.requests.failed", 1.0, {"path": request.path, "error": type(error).__name__}
        )


__all__ = ["ObservabilityMiddleware"]
