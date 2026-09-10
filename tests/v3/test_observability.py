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


class _SpanCatcher:
    """Tracer recording span names and attributes."""

    def __init__(self) -> None:
        """Initialize empty records."""
        self.spans: list[tuple[str, dict]] = []

    def span(self, name, attributes=None):
        """Open a recording span.

        Args:
            name: Span name.
            attributes: Initial attributes.

        Returns:
            Context manager yielding a recording span.
        """
        from contextlib import contextmanager

        catcher = self

        @contextmanager
        def _span():
            span = _RecordingSpan()
            catcher.spans.append((name, attributes or {}, span))
            yield span

        return _span()


class _RecordingSpan:
    """Span recording attribute writes."""

    def __init__(self) -> None:
        """Initialize empty attributes."""
        self.attributes: dict = {}

    def set_attribute(self, key, value) -> None:
        """Record an attribute.

        Args:
            key: Attribute name.
            value: Attribute value.
        """
        self.attributes[key] = value

    def record_exception(self, error) -> None:
        """Record an exception marker.

        Args:
            error: The failure.
        """
        self.attributes["exception"] = type(error).__name__


def test_spans_carry_outcome_and_correlation():
    """Spans record outcome, duration, and correlation IDs."""
    catcher = _SpanCatcher()
    middleware = ObservabilityMiddleware(catcher, InMemoryMeter())
    request = _request()
    middleware.before_send(request)
    middleware.after_send(request, Response(status_code=200, data={}))
    assert len(catcher.spans) == 1
    name, initial, span = catcher.spans[0]
    assert name == "whatsloon.request"
    assert initial["outcome"] == "success"
    assert initial["http.status_code"] == 200
    assert span.attributes["correlation_id"] == request.correlation_id


def test_concurrent_middleware_use_is_safe():
    """Concurrent sends through one middleware keep positive counts."""
    import threading

    meter = InMemoryMeter()
    middleware = ObservabilityMiddleware(NoOpTracer(), meter)
    request = _request()

    def _cycle():
        for _ in range(25):
            middleware.before_send(request)
            middleware.after_send(request, Response(status_code=200, data={}))

    threads = [threading.Thread(target=_cycle) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert meter.count("whatsloon.requests.started", {"path": "/123/messages"}) == 100.0
    assert (
        meter.count(
            "whatsloon.requests.completed",
            {"path": "/123/messages", "status": 200, "outcome": "success"},
        )
        == 100.0
    )


def test_failing_observer_never_breaks_sends(monkeypatch):
    """Observer exceptions are contained; the send still succeeds."""
    import httpx

    from whatsloon.config.settings import RetryConfig, TimeoutConfig
    from whatsloon.transport.request import Request as TransportRequest
    from whatsloon.transport.sync import SyncTransport

    class _Boom:
        def before_send(self, request) -> None:
            raise RuntimeError("telemetry down")

        def after_send(self, request, response) -> None:
            raise RuntimeError("telemetry down")

    def fake_request(self, method, url, **kwargs):
        request = httpx.Request(method, url)
        return httpx.Response(200, json={"messages": [{"id": "w-1"}]}, request=request)

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1, jitter=False),
        middleware=[_Boom()],
    )
    response = transport.send(TransportRequest(method="POST", path="/x", json_body={}))
    assert response.status_code == 200


def test_client_threads_middleware_to_transport(monkeypatch):
    """Client middleware param reaches the owned transport."""
    import httpx

    from whatsloon.client import WhatsApp
    from whatsloon.config.settings import RetryConfig, TimeoutConfig
    from whatsloon.transport.sync import SyncTransport

    seen = []

    class _Tap:
        def before_send(self, request) -> None:
            seen.append(request.path)

        def after_send(self, request, response) -> None:
            seen.append(response.status_code)

    def fake_request(self, method, url, **kwargs):
        request = httpx.Request(method, url)
        return httpx.Response(200, json={"messages": [{"id": "w-9"}]}, request=request)

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    tap = _Tap()
    client = WhatsApp(access_token="t", phone_number_id="123", middleware=[tap])
    try:
        assert client.transport.middleware == [tap]
        result = client.messages.send_text(to="919876543210", body="Hi")
        assert result.message_id == "w-9"
        assert seen[0] == "/123/messages" and seen[-1] == 200
    finally:
        client.close()
