"""Graph API version registry primitives.

``latest`` is a code pin resolving to :data:`LATEST_VERSION`, never a network
lookup. Adapters register against this module so applications can pin
``v19.0`` or ``v26.0`` without silent upgrades.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import ClassVar, Optional


LATEST_VERSION: str = "v26.0"
"""Pinned current adapter; the ``latest`` alias resolves here."""

SUPPORTED_VERSIONS: tuple[str, ...] = ("v19.0", "v26.0")
"""Versions with first-class adapters in this release."""

DEPRECATED_VERSIONS: frozenset[str] = frozenset()
"""Versions that warn on use but keep working."""


@dataclass(frozen=True)
class GraphAPIVersion:
    """A validated Graph API version identifier.

    Attributes:
        value: Canonical version string such as ``"v26.0"``.

    Examples:
        >>> GraphAPIVersion("v19.0").value
        'v19.0'
        >>> GraphAPIVersion("latest").value
        'v26.0'
    """

    value: str

    _registry: ClassVar[dict[str, str]] = {}

    def __post_init__(self) -> None:
        """Normalize aliases and validate support.

        Raises:
            ConfigurationError: If the version is unknown.
        """
        from whatsloon.exceptions import ConfigurationError

        normalized = LATEST_VERSION if self.value == "latest" else self.value
        if normalized not in SUPPORTED_VERSIONS:
            raise ConfigurationError(
                f"Unsupported graph_api_version={self.value!r}. "
                f"Supported: {list(SUPPORTED_VERSIONS)} plus 'latest'."
            )
        object.__setattr__(self, "value", normalized)
        if normalized in DEPRECATED_VERSIONS:
            warnings.warn(
                f"graph_api_version={normalized!r} is deprecated.",
                DeprecationWarning,
                stacklevel=3,
            )

    @property
    def is_latest(self) -> bool:
        """Whether this version is the pinned latest.

        Returns:
            True when equal to :data:`LATEST_VERSION`.
        """
        return self.value == LATEST_VERSION


@dataclass(frozen=True)
class VersionInfo:
    """Support status for one adapter version.

    Attributes:
        version: Version string.
        status: One of ``supported``, ``deprecated``, or ``planned``.
        serves_traffic: Whether Meta still serves this version. ``None``
            means unknown; adapter existence never implies serving.
        notes: Human-readable context.
    """

    version: str
    status: str = "supported"
    serves_traffic: Optional[bool] = None
    notes: str = ""


VERSION_MATRIX: tuple[VersionInfo, ...] = (
    VersionInfo(
        version="v19.0",
        status="supported",
        serves_traffic=None,
        notes="Legacy baseline wrapper; kept even after Meta EOL.",
    ),
    VersionInfo(
        version="v26.0",
        status="supported",
        serves_traffic=True,
        notes="Pinned current adapter; 'latest' resolves here.",
    ),
)
"""Published support matrix; adapter existence never implies Meta serving."""


def resolve_version(version: str) -> GraphAPIVersion:
    """Resolve a version string or ``latest`` alias.

    Args:
        version: Version string or ``"latest"``.

    Returns:
        Validated :class:`GraphAPIVersion`.

    Raises:
        ConfigurationError: If the version is unknown.
    """
    return GraphAPIVersion(version)
