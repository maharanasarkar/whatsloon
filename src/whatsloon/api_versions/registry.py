"""Version adapter registry.

``latest`` resolves to :data:`LATEST_VERSION` in code, never via network.
Pinned versions are never silently upgraded.
"""

from __future__ import annotations

from typing import Optional

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.api_versions.v19_0.adapter import V19Adapter
from whatsloon.api_versions.v20_0.adapter import V20Adapter
from whatsloon.api_versions.v26_0.adapter import V26Adapter
from whatsloon.config.versions import LATEST_VERSION, SUPPORTED_VERSIONS, GraphAPIVersion

_ADAPTERS: dict[str, type[VersionAdapter]] = {
    "v19.0": V19Adapter,
    "v20.0": V20Adapter,
    "v26.0": V26Adapter,
}
"""Adapter classes keyed by canonical version."""


def get_adapter(version: str) -> VersionAdapter:
    """Return an adapter instance for a version or ``latest`` alias.

    Args:
        version: Version string such as ``"v19.0"`` or ``"latest"``.

    Returns:
        Version adapter instance.

    Raises:
        ConfigurationError: If the version is unknown.
    """
    resolved = GraphAPIVersion(version).value
    return _ADAPTERS[resolved]()


def supported_versions() -> tuple[str, ...]:
    """List canonical supported versions.

    Returns:
        Supported version strings.
    """
    return SUPPORTED_VERSIONS


def latest_version() -> str:
    """Return the pinned latest version.

    Returns:
        Pinned latest version string.
    """
    return LATEST_VERSION


def adapter_status(version: str) -> dict[str, Optional[bool | str]]:
    """Describe support status for a version.

    Args:
        version: Version string or ``"latest"``.

    Returns:
        Mapping with version, status, and serving knowledge.
    """
    from whatsloon.config.versions import VERSION_MATRIX

    resolved = GraphAPIVersion(version).value
    for info in VERSION_MATRIX:
        if info.version == resolved:
            return {
                "version": info.version,
                "status": info.status,
                "serves_traffic": info.serves_traffic,
                "notes": info.notes,
            }
    return {"version": resolved, "status": "supported", "serves_traffic": None, "notes": ""}


__all__ = ["adapter_status", "get_adapter", "latest_version", "supported_versions"]
