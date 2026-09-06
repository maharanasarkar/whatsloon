"""Version adapters package."""

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.api_versions.registry import (
    adapter_status,
    get_adapter,
    latest_version,
    supported_versions,
)

__all__ = [
    "VersionAdapter",
    "adapter_status",
    "get_adapter",
    "latest_version",
    "supported_versions",
]
