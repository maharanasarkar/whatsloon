"""Authentication package."""

from whatsloon.auth.credentials import Credentials
from whatsloon.auth.providers import (
    CredentialProvider,
    EnvCredentialProvider,
    StaticCredentialProvider,
)

__all__ = [
    "CredentialProvider",
    "Credentials",
    "EnvCredentialProvider",
    "StaticCredentialProvider",
]
