"""Rate limiter and circuit breaker tests with fake clocks."""

import pytest

from whatsloon.exceptions import ConnectError, ValidationAPIError
from whatsloon.reliability.circuit import CircuitBreaker, CircuitOpenError, CircuitState
from whatsloon.reliability.rate import RateLimiter


class FakeClock:
    """Controllable monotonic clock.

    Attributes:
        now: Current reading.
    """

    def __init__(self) -> None:
        """Initialize at zero."""
        self.now = 0.0
        self.slept = 0.0

    def __call__(self) -> float:
        """Return the current reading.

        Returns:
            Current time.
        """
        return self.now

    def sleep(self, seconds: float) -> None:
        """Advance the clock instead of sleeping.

        Args:
            seconds: Seconds to advance.
        """
        self.slept += seconds
        self.now += seconds


def test_bucket_burst_then_refill():
    """Bursts pass up to capacity; refill restores tokens."""
    clock = FakeClock()
    limiter = RateLimiter(2.0, 2, clock=clock, sleeper=clock.sleep)
    assert limiter.try_acquire() and limiter.try_acquire()
    assert limiter.try_acquire() is False
    assert limiter.wait_time() == pytest.approx(0.5)
    clock.now += 1.0
    assert limiter.try_acquire() and limiter.try_acquire()


def test_acquire_waits_without_oversleep():
    """Blocking acquire sleeps exactly the deficit."""
    clock = FakeClock()
    limiter = RateLimiter(1.0, 1, clock=clock, sleeper=clock.sleep)
    limiter.acquire()
    limiter.acquire()
    assert clock.slept == pytest.approx(1.0)


def test_invalid_limiter_config_rejected():
    """Non-positive rates and capacities raise."""
    with pytest.raises(ValueError):
        RateLimiter(0, 1)
    with pytest.raises(ValueError):
        RateLimiter(1, 0)


def test_breaker_trips_and_recovers():
    """Threshold trips open; cooldown allows a half-open trial."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=10.0, clock=clock)
    assert breaker.call(lambda: "ok") == "ok"
    for _ in range(2):
        with pytest.raises(ConnectError):
            breaker.call(lambda: (_ for _ in ()).throw(ConnectError()))
    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "never")
    clock.now += 10.0
    assert breaker.state == CircuitState.HALF_OPEN
    assert breaker.call(lambda: "recovered") == "recovered"
    assert breaker.state == CircuitState.CLOSED


def test_breaker_ignores_validation_errors():
    """Client errors never trip the breaker."""
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=60.0)
    for _ in range(5):
        with pytest.raises(ValidationAPIError):
            breaker.call(lambda: (_ for _ in ()).throw(ValidationAPIError("bad")))
    assert breaker.state == CircuitState.CLOSED


def test_half_open_failure_reopens():
    """Failed trials return the breaker to open."""
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=5.0, clock=clock)
    with pytest.raises(ConnectError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectError()))
    clock.now += 5.0
    with pytest.raises(ConnectError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectError()))
    assert breaker.state == CircuitState.OPEN
