"""Fixtures for the authentication test suite."""

import pytest


@pytest.fixture(name="upstream_oidc_mocks")
def upstream_oidc_mocks_fixture(settings, responses):
    """Fixture that mock HTTP calls to an upstream OIDC Provider."""
    settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT = "http://upstream-oidc.test"

    well_known = {
        "issuer": settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT,
        "introspection_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/introspect/",
    }
    responses.add(
        responses.GET,
        f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/.well-known/openid-configuration",
        json=well_known,
        status=200,
    )
