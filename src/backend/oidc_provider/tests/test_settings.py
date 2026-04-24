"""Unit tests for OIDC provider settings helpers."""

import pytest

from oidc_provider.settings import OIDCProviderSettings, _value_format_pem_str


class DummyOIDCProviderSettings(OIDCProviderSettings):
    """Minimal test double for OIDC settings mixin."""

    def __init__(self, environment: str, private_key: str | None = None):
        """Initialize the OIDCProviderSettings object."""
        # pylint: disable=invalid-name
        self.ENVIRONMENT = environment
        self._OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY = private_key


def test_value_format_pem_str_returns_none_for_none_value():
    """None input should be passed through unchanged."""
    assert _value_format_pem_str(None) is None


def test_value_format_pem_str_formats_valid_pem_value():
    """A valid PEM should keep its delimiters and normalized body."""
    value = "-----BEGIN RSA PRIVATE KEY-----\nABCD\nEFGH\n-----END RSA PRIVATE KEY-----"

    assert _value_format_pem_str(value) == (
        "-----BEGIN RSA PRIVATE KEY-----\nABCDEFGH\n-----END RSA PRIVATE KEY-----\n"
    )


def test_value_format_pem_str_strips_wrapping_quotes_and_body_whitespace():
    """Wrapping quotes and body whitespace should be removed."""
    value = (
        "  '-----BEGIN RSA PRIVATE KEY-----\n"
        "AB CD\tEF\n"
        "-----END RSA PRIVATE KEY-----'  "
    )

    assert _value_format_pem_str(value) == (
        "-----BEGIN RSA PRIVATE KEY-----\nABCDEF\n-----END RSA PRIVATE KEY-----\n"
    )


def test_value_format_pem_str_wraps_body_at_64_characters():
    """PEM body should be wrapped on 64-char lines."""
    body = "A" * 70
    value = f"-----BEGIN RSA PRIVATE KEY-----\n{body}\n-----END RSA PRIVATE KEY-----"

    assert _value_format_pem_str(value) == (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        f"{'A' * 64}\n"
        f"{'A' * 6}\n"
        "-----END RSA PRIVATE KEY-----\n"
    )


def test_value_format_pem_str_formats_single_line_pem_value():
    """A single-line PEM input should be normalized to standard multi-line format."""
    value = "-----BEGIN RSA PRIVATE KEY----- ABCD EFGH -----END RSA PRIVATE KEY-----"

    assert _value_format_pem_str(value) == (
        "-----BEGIN RSA PRIVATE KEY-----\nABCDEFGH\n-----END RSA PRIVATE KEY-----\n"
    )


def test_value_format_pem_str_raises_error_for_invalid_pem():
    """Invalid input should raise a clear error."""
    with pytest.raises(ValueError, match="Invalid PEM format"):
        _value_format_pem_str("not a pem value")


def test_value_format_pem_str_raises_error_for_mismatched_key_type():
    """BEGIN/END mismatch should be rejected."""
    value = "-----BEGIN RSA PRIVATE KEY-----\nABCD\n-----END EC PRIVATE KEY-----"

    with pytest.raises(ValueError, match="Invalid PEM format"):
        _value_format_pem_str(value)


def test_get_oidc_rsa_private_key_returns_configured_key_in_production():
    """Configured key should always take precedence."""

    settings = DummyOIDCProviderSettings(
        environment="production",
        private_key="configured-private-key",
    )

    assert settings.OAUTH2_PROVIDER["OIDC_RSA_PRIVATE_KEY"] == "configured-private-key"


def test_get_oidc_rsa_private_key_generates_key_in_development(monkeypatch):
    """Development environment can use an ephemeral key."""

    settings = DummyOIDCProviderSettings(environment="development")
    monkeypatch.setattr(
        settings,
        "generate_temporary_rsa_key",
        lambda: "generated-development-key",
    )

    assert (
        settings.OAUTH2_PROVIDER["OIDC_RSA_PRIVATE_KEY"] == "generated-development-key"
    )


def test_get_oidc_rsa_private_key_generates_key_in_test(monkeypatch):
    """Test environment can use an ephemeral key."""

    settings = DummyOIDCProviderSettings(environment="test")
    monkeypatch.setattr(
        settings,
        "generate_temporary_rsa_key",
        lambda: "generated-test-key",
    )

    assert settings.OAUTH2_PROVIDER["OIDC_RSA_PRIVATE_KEY"] == "generated-test-key"


def test_get_oidc_rsa_private_key_raises_without_key_in_production():
    """Production-like environment must define a private key."""

    settings = DummyOIDCProviderSettings(environment="production")

    with pytest.raises(
        ValueError,
        match=(
            "OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY must be configured outside "
            "development and test environments."
        ),
    ):
        _ = settings.OAUTH2_PROVIDER
