"""Meter abstractions with an in-memory test implementation."""

from __future__ import annotations

from typing import Any, Protocol


class Meter(Protocol):
    """Record counters and latency distributions."""

    def increment(
        self, name: str, value: float = 1.0, attributes: dict[str, Any] | None = None
    ) -> None:
        """Add to a counter.

        Args:
            name: Metric name.
            value: Increment amount.
            attributes: Metric attributes.
        """
        ...  # pragma: no cover

    def observe(self, name: str, value: float, attributes: dict[str, Any] | None = None) -> None:
        """Record a latency or size observation.

        Args:
            name: Metric name.
            value: Observed value.
            attributes: Metric attributes.
        """
        ...  # pragma: no cover


class InMemoryMeter:
    """Test meter retaining every recording.

    Attributes:
        counters: Counter values keyed by (name, sorted attributes).
        observations: Observation lists keyed by (name, sorted attributes).
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self.counters: dict[tuple[str, tuple], float] = {}
        self.observations: dict[tuple[str, tuple], list[float]] = {}

    @staticmethod
    def _key(name: str, attributes: dict[str, Any] | None) -> tuple[str, tuple]:
        """Build a storage key.

        Args:
            name: Metric name.
            attributes: Metric attributes.

        Returns:
            Hashable key.
        """
        return (name, tuple(sorted((attributes or {}).items())))

    def increment(
        self, name: str, value: float = 1.0, attributes: dict[str, Any] | None = None
    ) -> None:
        """Add to a counter.

        Args:
            name: Metric name.
            value: Increment amount.
            attributes: Metric attributes.
        """
        key = self._key(name, attributes)
        self.counters[key] = self.counters.get(key, 0.0) + value

    def observe(self, name: str, value: float, attributes: dict[str, Any] | None = None) -> None:
        """Record a latency or size observation.

        Args:
            name: Metric name.
            value: Observed value.
            attributes: Metric attributes.
        """
        key = self._key(name, attributes)
        self.observations.setdefault(key, []).append(value)

    def count(self, name: str, attributes: dict[str, Any] | None = None) -> float:
        """Read a counter value.

        Args:
            name: Metric name.
            attributes: Metric attributes.

        Returns:
            Accumulated value or zero.
        """
        return self.counters.get(self._key(name, attributes), 0.0)


class NoOpMeter:
    """Meter that discards all recordings."""

    def increment(
        self, name: str, value: float = 1.0, attributes: dict[str, Any] | None = None
    ) -> None:
        """Discard a counter increment.

        Args:
            name: Metric name.
            value: Increment amount.
            attributes: Metric attributes.
        """

    def observe(self, name: str, value: float, attributes: dict[str, Any] | None = None) -> None:
        """Discard an observation.

        Args:
            name: Metric name.
            value: Observed value.
            attributes: Metric attributes.
        """


__all__ = ["InMemoryMeter", "Meter", "NoOpMeter"]
