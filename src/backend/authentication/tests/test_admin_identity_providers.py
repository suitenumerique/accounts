"""Tests for the identity providers admin."""

import html
import json
import re

from django.urls import reverse

import pytest

from core.factories import UserFactory

from authentication.admin import get_displayed_claims
from authentication.factories import IdentityProviderUserFactory
from authentication.models import IdentityProviderUser

pytestmark = pytest.mark.django_db

SECRET_EXTRA_DATA = {
    "access_token": "secret-access-token",
    "refresh_token": "secret-refresh-token",
    "id_token": "secret-id-token",
}
BACKEND_EXTRA_DATA = {
    "auth_time": 1761220000,
    "token_type": "Bearer",
    "_oidc_id_token_context": {"sub": "idp-sub"},
}


@pytest.fixture(name="superuser_client")
def superuser_client_fixture(client):
    """Return a client logged in as a superuser."""
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    return client


def _displayed_claims(content):
    """Return the claims displayed as JSON in the first `<pre>` of the page."""
    match = re.search(r"<pre>(.*?)</pre>", content, re.S)
    assert match, "No claims displayed"
    return json.loads(html.unescape(match.group(1)))


@pytest.mark.parametrize(
    "extra_data,expected_claims",
    [
        (
            {"sub": "idp-sub", "roles": ["agent_public_territorial", "agent_public"]},
            {"sub": "idp-sub", "roles": ["agent_public_territorial", "agent_public"]},
        ),
        ({"roles": []}, {"roles": []}),
        ({"roles": None}, {"roles": None}),
        ({"siret": "1234567890123"}, {"siret": "1234567890123"}),
        ({}, {}),
    ],
)
def test_get_displayed_claims(extra_data, expected_claims):
    """Only the backend `EXTRA_DATA` claims are displayed."""
    identity_provider = IdentityProviderUser(
        provider="pro-connect",
        extra_data={**extra_data, **SECRET_EXTRA_DATA, **BACKEND_EXTRA_DATA},
    )

    assert get_displayed_claims(identity_provider) == expected_claims


def test_get_displayed_claims_unknown_backend():
    """An identity provider without a configured backend displays no claims."""
    identity_provider = IdentityProviderUser(
        provider="unknown", extra_data={"roles": ["agent_public"]}
    )

    assert get_displayed_claims(identity_provider) == {}


def test_identity_provider_user_changelist_is_generic(superuser_client):
    """The list only shows generic columns, never the claims nor the tokens."""
    IdentityProviderUserFactory(
        uid="listed-sub",
        extra_data={"roles": ["agent_public"], **SECRET_EXTRA_DATA},
    )

    response = superuser_client.get(
        reverse("admin:authentication_identityprovideruser_changelist")
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "listed-sub" in content
    assert "agent_public" not in content
    for secret in SECRET_EXTRA_DATA.values():
        assert secret not in content


def test_identity_provider_user_change_view_shows_claims(superuser_client):
    """The detail page shows the claims, and never the tokens."""
    identity_provider = IdentityProviderUserFactory(
        extra_data={"roles": [], "siret": "1234567890123", **SECRET_EXTRA_DATA}
    )

    response = superuser_client.get(
        reverse(
            "admin:authentication_identityprovideruser_change",
            args=[identity_provider.pk],
        )
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert _displayed_claims(content) == {"roles": [], "siret": "1234567890123"}
    for secret in SECRET_EXTRA_DATA.values():
        assert secret not in content


def test_identity_provider_user_admin_is_read_only(superuser_client):
    """Identity provider associations cannot be added nor changed from the admin."""
    identity_provider = IdentityProviderUserFactory()

    add_response = superuser_client.get(
        reverse("admin:authentication_identityprovideruser_add")
    )
    change_response = superuser_client.post(
        reverse(
            "admin:authentication_identityprovideruser_change",
            args=[identity_provider.pk],
        ),
        {"uid": "changed-uid"},
    )

    assert add_response.status_code == 403
    assert change_response.status_code == 403
    identity_provider.refresh_from_db()
    assert identity_provider.uid != "changed-uid"


def test_user_admin_shows_identity_providers_inline(superuser_client):
    """The user change page lists its identity providers with their claims."""
    identity_provider = IdentityProviderUserFactory(
        uid="inline-sub",
        extra_data={"roles": ["agent_public"], **SECRET_EXTRA_DATA},
    )

    response = superuser_client.get(
        reverse("admin:users_user_change", args=[identity_provider.user.pk])
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "ProConnect - inline-sub" in content
    assert _displayed_claims(content) == {"roles": ["agent_public"]}
    for secret in SECRET_EXTRA_DATA.values():
        assert secret not in content
