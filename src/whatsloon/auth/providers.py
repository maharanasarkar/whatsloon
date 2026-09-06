"""Credentials and credential providers.

Credentials flow through explicit configuration and tenant-aware providers,
never global mutable state, and never into logs or persistence tables.
"""

from __future__ import annotations

import os
from typing import Optional, Protocol

from whatsloon.auth.credentials import Credentials


class CredentialProvider(Protocol):
    """Resolve credentials for a WhatsApp tenant."""

    def get_credentials(self, tenant_id: str) -> Credentials:
        """Return credentials for the given tenant.

        Args:
            tenant_id: Application-level tenant identifier.

        Returns:
            Resolved WhatsApp credentials.
        """
        ...  # pragma: no cover


class StaticCredentialProvider:
    """Serve one fixed credential set for every tenant.

    Attributes:
        credentials: Credentials returned for any tenant.
    """

    def __init__(self, credentials: Credentials) -> None:
        """Initialize the provider.

        Args:
            credentials: Credentials returned for any tenant.
        """
        self.credentials = credentials

    def get_credentials(self, tenant_id: str) -> Credentials:
        """Return the static credentials.

        Args:
            tenant_id: Ignored; static credentials serve all tenants.

        Returns:
            The configured credentials.
        """
        return self.credentials


class EnvCredentialProvider:
    """Resolve credentials from environment variables.

    Attributes:
        tenant_id: Default tenant identifier attached to credentials.
    """

    def __init__(
        self,
        *,
        tenant_id: Optional[str] = None,
        token_var: str = "WHATSAPP_ACCESS_TOKEN",
        phone_var: str = "WHATSAPP_PHONE_NUMBER_ID",
        secret_var: str = "WHATSAPP_APP_SECRET",
    ) -> None:
        """Initialize the provider.

        Args:
            tenant_id: Default tenant identifier.
            token_var: Environment variable for the access token.
            phone_var: Environment variable for the phone number ID.
            secret_var: Environment variable for the app secret.
        """
        self.tenant_id = tenant_id
        self.token_var = token_var
        self.phone_var = phone_var
        self.secret_var = secret_var

    def get_credentials(self, tenant_id: str) -> Credentials:
        """Read credentials from the environment.

        Args:
            tenant_id: Tenant identifier attached when no default is set.

        Returns:
            Credentials resolved from environment variables.

        Raises:
            ConfigurationError: If required variables are missing.
        """
        from whatsloon.exceptions import ConfigurationError

        token = os.environ.get(self.token_var)
        phone_id = os.environ.get(self.phone_var)
        if not token or not phone_id:
            raise ConfigurationError(
                f"Missing {self.token_var} or {self.phone_var} in the environment."
            )
        return Credentials(
            access_token=token,
            phone_number_id=phone_id,
            tenant_id=self.tenant_id or tenant_id,
            app_secret=os.environ.get(self.secret_var),
        )
