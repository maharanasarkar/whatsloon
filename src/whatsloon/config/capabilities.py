"""Version capability flags.

Capabilities answer "does this adapter support X?" so feature code never
branches on raw version strings.
"""

from __future__ import annotations

from pydantic import BaseModel


class VersionCapabilities(BaseModel):
    """Feature flags for one Graph API adapter.

    Attributes:
        calls: Whether calling APIs are supported.
        groups: Whether group APIs are supported.
        flows: Whether Flow message composition is supported.
        direct_send: Whether Direct Send is supported.
        commerce: Whether commerce/QR surfaces are supported.
    """

    calls: bool = False
    groups: bool = False
    flows: bool = True
    direct_send: bool = False
    commerce: bool = False


CAPABILITIES: dict[str, VersionCapabilities] = {
    "v19.0": VersionCapabilities(),
    "v26.0": VersionCapabilities(calls=True, groups=True, direct_send=True),
}
"""Capability map keyed by canonical version string."""


def get_capabilities(version: str) -> VersionCapabilities:
    """Return capability flags for a version.

    Args:
        version: Canonical version string.

    Returns:
        Capability flags; unknown versions get conservative defaults.
    """
    return CAPABILITIES.get(version, VersionCapabilities())
