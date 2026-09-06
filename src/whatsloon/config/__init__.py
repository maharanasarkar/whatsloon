"""Configuration package."""

from whatsloon.config.capabilities import CAPABILITIES, VersionCapabilities, get_capabilities
from whatsloon.config.retry import backoff_delay, is_retryable_status, parse_retry_after
from whatsloon.config.settings import RetryConfig, TimeoutConfig, WhatsAppConfig
from whatsloon.config.versions import (
    DEPRECATED_VERSIONS,
    LATEST_VERSION,
    SUPPORTED_VERSIONS,
    VERSION_MATRIX,
    GraphAPIVersion,
    VersionInfo,
    resolve_version,
)

__all__ = [
    "CAPABILITIES",
    "DEPRECATED_VERSIONS",
    "LATEST_VERSION",
    "SUPPORTED_VERSIONS",
    "VERSION_MATRIX",
    "GraphAPIVersion",
    "RetryConfig",
    "TimeoutConfig",
    "VersionCapabilities",
    "VersionInfo",
    "WhatsAppConfig",
    "backoff_delay",
    "get_capabilities",
    "is_retryable_status",
    "parse_retry_after",
    "resolve_version",
]
