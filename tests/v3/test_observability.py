"""Observability middleware tests with controllable clocks."""

from whatsloon.exceptions import ConnectError
from whatsloon.observability.metrics import InMemoryMeter, NoOpMeter
from whatsloon.observability.middleware import ObservabilityMiddleware
from whatsloon.observability.tracing import NoOpTracer
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response


class FakeClock:
    """Controllable clock.

    Attributes:
        now: Current reading.
    """

    def __init__(self) -> None:
        """Initialize at zero."""
        self.now = 100.0

    def __call__(self) -> float:
        """Return the current reading.

        Returns:
            Current time.
        """
        return self.now


def _request():
    """Build a sample request.

    Returns:
        Sample request.
    """
    return Request(method="POST", path="/123/messages", json_body={})


def test_success_records_counters_and_latency():
    """Completed requests record outcome counters and durations."""
    clock = FakeClock()
    meter = InMemoryMeter()
    middleware = ObservabilityMiddleware(NoOpTracer(), meter, clock=clock)
    request = _request()
    middleware.before_send(request)
    clock.now += 0.25
    middleware.after_send(request, Response(status_code=200, data={}))
    assert meter.count("whatsloon.requests.started", {"path": "/123/messages"}) == 1.0
    assert (
        meter.count(
            "whatsloon.requests.completed",
            {"path": "/123/messages", "status": 200, "outcome": "success"},
        )
        == 1.0
    )
    key = (
        "whatsloon.requests.duration_seconds",
        (("outcome", "success"), ("path", "/123/messages")),
    )
    assert meter.observations[key] == [0.25]


def test_error_outcome_and_failure_paths():
    """Error statuses and transport failures record distinctly."""
    meter = InMemoryMeter()
    middleware = ObservabilityMiddleware(NoOpTracer(), meter)
    request = _request()
    middleware.before_send(request)
    middleware.after_send(request, Response(status_code=500, data={}))
    assert (
        meter.count(
            "whatsloon.requests.completed",
            {"path": "/123/messages", "status": 500, "outcome": "error"},
        )
        == 1.0
    )
    middleware.record_error(_request(), ConnectError())
    assert (
        meter.count(
            "whatsloon.requests.failed",
            {"path": "/123/messages", "error": "ConnectError"},
        )
        == 1.0
    )


def test_noop_defaults_are_safe():
    """Default middleware never raises without telemetry backends."""
    middleware = ObservabilityMiddleware()
    request = _request()
    middleware.before_send(request)
    middleware.after_send(request, Response(status_code=200, data={}))
    middleware.record_error(request, ConnectError())
    assert isinstance(middleware.meter, NoOpMeter)
