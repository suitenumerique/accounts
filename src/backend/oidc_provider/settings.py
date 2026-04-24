"""
Django settings dedicated to oidc_provider application.
"""

import re
import textwrap
from typing import Any, Dict, Optional

from configurations import values
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

TEMPORARY_OIDC_RSA_KEY_ALLOWED_ENVIRONMENTS = {
    "development",
    "test",
    "continuousintegration",
    "build",
}


def _value_format_pem_str(value: Optional[str]) -> Optional[str]:
    """
    Receive a bad formatted PEM string and convert it to good formatted PEM string.

    Note, this is a formatter, not a validator.
    """

    if value is None:
        return value

    normalized = value.strip()
    normalized = normalized.strip().strip('"').strip("'")

    # Convert the characters escape: met them in the tilt stack...
    normalized = (
        normalized.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    )
    normalized = "".join(normalized.splitlines())

    pem_match = re.search(
        r"-----BEGIN (?P<key_type>[^-]+)-----(?P<pem_body>.*?)-----END (?P=key_type)-----",
        normalized,
        flags=re.DOTALL,
    )
    if not pem_match:
        raise ValueError("Invalid PEM format")

    key_type = pem_match.group("key_type")
    pem_body = re.sub(r"\s+", "", pem_match.group("pem_body"))
    wrapped_body = "\n".join(textwrap.wrap(pem_body, 64))

    return f"-----BEGIN {key_type}-----\n{wrapped_body}\n-----END {key_type}-----\n"


class PEMValue(values.Value):
    """
    Django configurations value for PEM-formatted strings, with automatic formatting correction.
    """

    def to_python(self, value):
        """Normalize PEM-formatted environment values."""

        return _value_format_pem_str(value)


class OIDCProviderSettings:
    """
    OIDC Provider settings: this allows OIDC authentication from products through this project.
    """

    _OAUTH2_PROVIDER_OIDC_ENABLED = values.BooleanValue(
        default=True,
        environ_name="OAUTH2_PROVIDER_OIDC_ENABLED",
        environ_prefix=None,
    )

    _OAUTH2_PROVIDER_SCOPES = values.DictValue(
        default={
            "openid": "OpenID Connect",
            "profile": "Profile information",
            "email": "Email address",
        },
        environ_name="OAUTH2_PROVIDER_SCOPES",
        environ_prefix=None,
    )
    _OAUTH2_PROVIDER_PKCE_REQUIRED = values.BooleanValue(
        default=False,  # For backward compatibility ProConnect
        environ_name="OAUTH2_PROVIDER_PKCE_REQUIRED",
        environ_prefix=None,
    )
    _OAUTH2_PROVIDER_ACCESS_TOKEN_EXPIRE_SECONDS = values.IntegerValue(
        default=60 * 60,  # 1 hour
        environ_name="OAUTH2_PROVIDER_ACCESS_TOKEN_EXPIRE_SECONDS",
        environ_prefix=None,
    )
    _OAUTH2_PROVIDER_REFRESH_TOKEN_EXPIRE_SECONDS = values.IntegerValue(
        default=24 * 60 * 60,  # 24 hours
        environ_name="OAUTH2_PROVIDER_REFRESH_TOKEN_EXPIRE_SECONDS",
        environ_prefix=None,
    )
    _OAUTH2_PROVIDER_AUTHORIZATION_CODE_EXPIRE_SECONDS = values.IntegerValue(
        default=5 * 60,  # 5 minutes
        environ_name="OAUTH2_PROVIDER_AUTHORIZATION_CODE_EXPIRE_SECONDS",
        environ_prefix=None,
    )

    _OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY = PEMValue(
        default=None,
        environ_name="OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY",
        environ_prefix=None,
    )
    _OAUTH2_PROVIDER_OAUTH2_VALIDATOR_CLASS = values.Value(
        default="oauth2_provider.oauth2_validators.OAuth2Validator",
        environ_name="OAUTH2_PROVIDER_OAUTH2_VALIDATOR_CLASS",
        environ_prefix=None,
    )

    _OAUTH2_PROVIDER_ALLOWED_REDIRECT_URI_SCHEMES = values.ListValue(
        default=["http", "https"],
        environ_name="OAUTH2_PROVIDER_ALLOWED_REDIRECT_URI_SCHEMES",
        environ_prefix=None,
    )

    _OAUTH2_PROVIDER_ROTATE_REFRESH_TOKEN = values.BooleanValue(
        default=True,
        environ_name="OAUTH2_PROVIDER_ROTATE_REFRESH_TOKEN",
        environ_prefix=None,
    )

    @classmethod
    def generate_temporary_rsa_key(cls):
        """Generate a temporary RSA key for OIDC Provider."""

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        # - Serialize private key to PEM format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        return private_key_pem.decode("utf-8")

    def _get_oidc_rsa_private_key(self) -> str:
        """Return configured RSA key, or generate one when explicitly allowed."""

        configured_private_key = self._OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY
        if configured_private_key:
            return str(configured_private_key)

        environment = str(getattr(self, "ENVIRONMENT", "")).lower()
        if environment in TEMPORARY_OIDC_RSA_KEY_ALLOWED_ENVIRONMENTS:
            return self.generate_temporary_rsa_key()

        raise ValueError(
            "OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY must be configured outside "
            "development and test environments."
        )

    @property
    def OAUTH2_PROVIDER(self) -> Dict[str, Any]:  # pylint: disable=invalid-name
        """Build the OAUTH2_PROVIDER settings dictionary based on the configuration provided."""

        return {
            "SCOPES": self._OAUTH2_PROVIDER_SCOPES,
            "PKCE_REQUIRED": self._OAUTH2_PROVIDER_PKCE_REQUIRED,
            # Token expiration settings
            "ACCESS_TOKEN_EXPIRE_SECONDS": self._OAUTH2_PROVIDER_ACCESS_TOKEN_EXPIRE_SECONDS,
            "REFRESH_TOKEN_EXPIRE_SECONDS": self._OAUTH2_PROVIDER_REFRESH_TOKEN_EXPIRE_SECONDS,
            "AUTHORIZATION_CODE_EXPIRE_SECONDS": (
                self._OAUTH2_PROVIDER_AUTHORIZATION_CODE_EXPIRE_SECONDS
            ),
            # OIDC configuration
            "OIDC_ENABLED": self._OAUTH2_PROVIDER_OIDC_ENABLED,
            "OIDC_RSA_PRIVATE_KEY": self._get_oidc_rsa_private_key(),
            "OAUTH2_VALIDATOR_CLASS": self._OAUTH2_PROVIDER_OAUTH2_VALIDATOR_CLASS,
            # Redirection URI schemes allowed for authorization code flow.
            # By default, only http and https are allowed, but you can add custom schemes
            # if needed (e.g., for mobile applications).
            "ALLOWED_REDIRECT_URI_SCHEMES": self._OAUTH2_PROVIDER_ALLOWED_REDIRECT_URI_SCHEMES,
            # Refresh token configuration
            "ROTATE_REFRESH_TOKEN": self._OAUTH2_PROVIDER_ROTATE_REFRESH_TOKEN,
        }
