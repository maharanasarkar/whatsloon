"""Version registry tests."""

import pytest

from whatsloon.api_versions.registry import (
    adapter_status,
    get_adapter,
    latest_version,
    supported_versions,
)
from whatsloon.api_versions.v19_0.adapter import V19Adapter
from whatsloon.api_versions.v20_0.adapter import V20Adapter
from whatsloon.api_versions.v26_0.adapter import V26Adapter
from whatsloon.config.versions import LATEST_VERSION, GraphAPIVersion
from whatsloon.exceptions import ConfigurationError


def test_latest_resolves_to_pin():
    """'latest' resolves to the checked-in pin, never a network lookup."""
    assert GraphAPIVersion("latest").value == LATEST_VERSION == "v26.0"
    assert latest_version() == "v26.0"


def test_unknown_version_rejected():
    """Unknown versions raise instead of silently changing behavior."""
    with pytest.raises(ConfigurationError):
        GraphAPIVersion("v99.0")


def test_registry_returns_isolated_adapters():
    """Each version maps to its own adapter class."""
    assert isinstance(get_adapter("v19.0"), V19Adapter)
    assert isinstance(get_adapter("v20.0"), V20Adapter)
    assert isinstance(get_adapter("v26.0"), V26Adapter)
    assert isinstance(get_adapter("latest"), V26Adapter)


def test_supported_versions_lists_all():
    """Registry exposes the full adapter matrix."""
    assert set(supported_versions()) == {"v19.0", "v20.0", "v26.0"}


def test_adapter_status_distinguishes_serving():
    """Status reports never conflate adapter existence with Meta serving."""
    status = adapter_status("v19.0")
    assert status["version"] == "v19.0"
    assert status["serves_traffic"] is None
    assert adapter_status("latest")["version"] == "v26.0"
