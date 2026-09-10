# Reliability and observability

## Pacing (`reliability.RateLimiter`)

```python
from whatsloon.reliability import RateLimiter

limiter = RateLimiter(rate_per_second=20.0, capacity=20)
limiter.acquire()
wa.messages.send_text(to="...", body="...")
```

Async variant: `AsyncRateLimiter` with `await limiter.acquire()`.

## Breakers (`reliability.CircuitBreaker`)

```python
from whatsloon.reliability import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=30.0)
breaker.call(lambda: wa.messages.send_text(to="...", body="..."))
```

Only transport and retryable API failures trip the breaker; validation and
auth errors pass through. Open circuits fail fast with `CircuitOpenError`;
after cooldown a single half-open trial decides recovery.

## Bulk sends (`reliability.BulkSender`)

```python
from whatsloon.messages.models import OutboundMessage, TextMessage
from whatsloon.reliability import BulkSender

sender = BulkSender(wa.messages, max_workers=5, limiter=limiter, breaker=breaker)
summary = sender.send_all(
    [OutboundMessage(to=to, content=TextMessage(body="Hi")) for to in recipients]
)
print(summary.sent, summary.failed)
```

Batches never abort: every envelope resolves to a per-item result in
submission order. Async variant: `AsyncBulkSender`.

## Observability (`whatsloon[observability]`)

```python
from whatsloon import WhatsApp
from whatsloon.observability import InMemoryMeter, NoOpTracer, ObservabilityMiddleware

middleware = ObservabilityMiddleware(NoOpTracer(), InMemoryMeter())
wa = WhatsApp(access_token="...", phone_number_id="...", middleware=[middleware])
```

The client threads observers through its owned transport, so every attempt
records spans, counters, and latency. Observer failures are logged, never
raised. Swap in `OpenTelemetryTracer.create()` for real spans; core stays
dependency-free via no-op defaults. Metrics: `whatsloon.requests.*`
counters and duration observations — no bodies or secrets recorded.
