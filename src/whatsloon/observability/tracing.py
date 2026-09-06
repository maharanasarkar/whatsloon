"""Tracer abstractions with safe no-op defaults.

Real OpenTelemetry wiring lives behind the ``observability`` extra; core
code depends only on these protocols.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Optional, Protocol


class Span(Protocol):
    """An active tracing span."""

    def set_attribute(self, key: str, value: Any) -> None:
        """Attach an attribute to the span.

        Args:
            key: Attribute name.
            value: Attribute value.
        """
        ...  # pragma: no cover

    def record_exception(self, error: BaseException) -> None:
        """Record an exception on the span.

        Args:
            error: The failure.
        """
        ...  # pragma: no cover


class Tracer(Protocol):
    """Create spans for SDK operations."""

    def span(self, name: str, attributes: Optional[dict[str, Any]] = None) -> Any:
        """Open a span context manager.

        Args:
            name: Span name.
            attributes: Initial attributes.

        Returns:
            Context manager yielding a span.
        """
        ...  # pragma: no cover


class _NoOpSpan:
    """Span that discards all telemetry."""

    def set_attribute(self, key: str, value: Any) -> None:
        """Discard an attribute.

        Args:
            key: Attribute name.
            value: Attribute value.
        """

    def record_exception(self, error: BaseException) -> None:
        """Discard an exception.

        Args:
            error: The failure.
        """


class NoOpTracer:
    """Tracer that disables tracing without code changes."""

    @contextmanager
    def span(self, name: str, attributes: Optional[dict[str, Any]] = None) -> Iterator[_NoOpSpan]:
        """Open a discarded span.

        Args:
            name: Span name.
            attributes: Ignored attributes.

        Yields:
            No-op span.
        """
        yield _NoOpSpan()


class OpenTelemetryTracer:
    """OTel-backed tracer (``whatsloon[observability]`` extra).

    Attributes:
        tracer: Underlying OTel tracer.
    """

    def __init__(self, tracer: Any) -> None:
        """Initialize with an OTel tracer.

        Args:
            tracer: ``opentelemetry.trace`` tracer.
        """
        self._tracer = tracer

    @classmethod
    def create(cls, name: str = "whatsloon") -> OpenTelemetryTracer:
        """Create a tracer from the global OTel provider.

        Args:
            name: Instrumentation scope name.

        Returns:
            Configured tracer.

        Raises:
            ImportError: If OpenTelemetry is not installed.
        """
        try:
            from opentelemetry import trace
        except ImportError as exc:
            raise ImportError(
                "Observability requires the extra: pip install 'whatsloon[observability]'."
            ) from exc
        return cls(trace.get_tracer(name))

    @contextmanager
    def span(self, name: str, attributes: Optional[dict[str, Any]] = None) -> Iterator[Any]:
        """Open an OTel span.

        Args:
            name: Span name.
            attributes: Initial attributes.

        Yields:
            Active OTel span.
        """
        with self._tracer.start_as_current_span(name, attributes=attributes or {}) as span:
            yield span


__all__ = ["NoOpTracer", "OpenTelemetryTracer", "Span", "Tracer"]
