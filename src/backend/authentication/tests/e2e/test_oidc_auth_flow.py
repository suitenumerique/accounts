"""
End-to-end tests for the complete OIDC authentication flow.

These tests verify that:
1. The full flow works: a product requests authentication from Accounts,
   Accounts redirects the user to the upstream OIDC provider, retrieves tokens,
   creates/updates the user, then returns an authorization code to the product.
2. When the user already has an active session, Accounts does not contact
   the upstream OIDC provider and directly grants the authorization code to the product.
"""

import re
from unittest import mock
from urllib.parse import parse_qs, urljoin, urlparse

from django.http import QueryDict
from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects

from core.factories import UserFactory

from oidc_provider.factories import (
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    SimpleApplicationFactory,
)
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture(name="upstream_oidc_mocks")
def upstream_oidc_mocks_fixture(settings, responses):
    """Fixture that mock HTTP calls to an upstream OIDC Provider."""
    settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT = "http://upstream-oidc.test"
    settings.SOCIAL_AUTH_PRO_CONNECT_KEY = "accounts-rp"
    settings.SOCIAL_AUTH_PRO_CONNECT_SECRET = "accounts-rp-secret"
    settings.LOGIN_REDIRECT_URL = "/"

    well_known = {
        "issuer": settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT,
        "authorization_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/authorize/",
        "token_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/token/",
        "userinfo_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/userinfo/",
        "end_session_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/logout/",
    }
    responses.add(
        responses.GET,
        re.compile(
            re.escape(
                f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/.well-known/openid-configuration"
            )
        ),
        json=well_known,
        status=200,
    )
    responses.add(
        responses.POST,
        re.compile(re.escape(well_known["token_endpoint"])),
        json={
            "access_token": "upstream-access-token",
            "id_token": "upstream-id-token",
            "refresh_token": "upstream-refresh-token",
            "token_type": "Bearer",
        },
        status=200,
    )


@pytest.mark.usefixtures("upstream_oidc_mocks")
def test_full_oidc_auth_flow_new_user(responses, settings, client):  # pylint: disable=too-many-locals
    """
    Verify the complete end-to-end OIDC authentication flow for a new user.

    Scenario:
    1. The product redirects the user to Accounts's authorization endpoint.
    2. Accounts redirects the user to the upstream OIDC provider.
    3. The upstream OIDC provider calls back Accounts with a code.
    4. Accounts exchanges the code for tokens (HTTP call to the upstream OIDC provider).
    5. Accounts creates the user and establishes a session.
    6. Accounts redirects the user to the product with an authorization code.
    7. The product exchanges this code for tokens from Accounts.

    Asserts that the upstream OIDC provider is contacted at least once (token +
    userinfo) and that a user is created in the database.
    """
    SimpleApplicationFactory()
    sub = "test-user-sub-123"

    # ---- Step 1: The product sends the user to Accounts's authorization endpoint ----
    oauth2_provider_authorize_url = reverse(
        "oauth2_provider:authorize",
        query={
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "openid email",
        },
    )
    oauth2_provider_authorize_response = client.get(oauth2_provider_authorize_url)

    # Accounts must redirect to login because the user is not authenticated
    authentication_login_url = reverse(
        "authentication:login", query={"next": oauth2_provider_authorize_url}
    )
    assertRedirects(
        oauth2_provider_authorize_response,
        authentication_login_url,
        fetch_redirect_response=False,
    )

    # Then we get redirected to the upstream OIDC provider
    oidc_upstream_response = client.get(authentication_login_url, follow=False)
    assert oidc_upstream_response.status_code == 302
    assert oidc_upstream_response.url.startswith(
        settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT
    )

    # Extract the `state` from the redirect URL
    callback_params = QueryDict(urlparse(oidc_upstream_response.url).query)
    assert callback_params["client_id"] == settings.SOCIAL_AUTH_PRO_CONNECT_KEY
    assert callback_params["redirect_uri"] == urljoin(
        "http://testserver",
        reverse("authentication:social:complete", kwargs={"backend": "pro-connect"}),
    )
    assert callback_params["scope"] == "openid email given_name usual_name siret"

    # ---- Step 2: The upstream OIDC provider calls back Accounts with an authorization code ----
    with (
        mock.patch(
            "social_core.backends.open_id_connect.OpenIdConnectAuth.validate_and_return_id_token",
            return_value={
                "sub": sub,
                "email": "testuser@example.com",
            },
        ),
        mock.patch(
            "authentication.backends.ProConnect.user_data",
            return_value={
                "sub": sub,
                "email": "testuser@example.com",
                "given_name": "Test",
                "usual_name": "User",
                "siret": "1234567890123",
            },
        ),
    ):
        callback_response = client.get(
            reverse(
                "authentication:social:complete", kwargs={"backend": "pro-connect"}
            ),
            {"code": "upstream-auth-code", "state": callback_params["state"]},
            follow=False,
        )

    # Accounts must redirect after successful authentication
    assertRedirects(
        callback_response, oauth2_provider_authorize_url, fetch_redirect_response=False
    )

    # The user must now be authenticated in the session
    user = User.objects.get()
    assert user.sub == sub
    assert user.email == "testuser@example.com"
    assert user.short_name == "Test"
    assert user.full_name == "Test User"
    assert user.identity_providers.get(provider="pro-connect").extra_data == {
        "access_token": "upstream-access-token",
        "auth_time": int(user.last_login.timestamp()),
        "email": "testuser@example.com",
        "email_verified": None,
        "given_name": "Test",
        "id_token": "upstream-id-token",
        "refresh_token": "upstream-refresh-token",
        "siret": "1234567890123",
        "sub": "test-user-sub-123",
        "token_type": "Bearer",
        "usual_name": "User",
    }

    # Follow the post-login redirect chain until we find the redirect to the product
    follow_response = client.get(callback_response.url, follow=True)
    # The last redirect must point to the product
    final_url = follow_response.redirect_chain[-1][0]
    assert final_url.startswith(REDIRECT_URI), (
        f"The final redirect must point to the product, got: {final_url}"
    )

    # Extract the authorization code returned to the product
    final_params = QueryDict(urlparse(final_url).query)

    # ---- Step 3: The product exchanges the code for tokens ----
    token_response = client.post(
        reverse("oauth2_provider:token"),
        {
            "grant_type": "authorization_code",
            "code": final_params["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    assert token_response.status_code == 200
    token_data = token_response.json()
    assert "access_token" in token_data
    assert "id_token" in token_data

    # Verify that the upstream OIDC provider was contacted (openid-configuration + token)
    assert [c.request.url for c in responses.calls] == [
        "http://upstream-oidc.test/.well-known/openid-configuration",
        "http://upstream-oidc.test/token/",
    ]


def test_oidc_auth_flow_existing_session_no_upstream_call(responses, settings, client):
    """
    Verify that Accounts does not contact the upstream OIDC provider when
    the user already has an active session.

    Scenario:
    1. A user is already authenticated (active session on Accounts).
    2. The product requests authorization from Accounts.
    3. Accounts directly grants the authorization code without going through the IdP.
    4. The product exchanges the code for tokens.

    Asserts that no HTTP call is made to the upstream OIDC provider.
    """
    SimpleApplicationFactory()

    # Create an existing user and log them in directly
    user = UserFactory()
    client.force_login(user)

    # ---- Step 1: The product sends the user to Accounts's authorization endpoint ----
    # The user is already logged in; Accounts must grant authorization directly
    oidc_provider_authorize_url = reverse(
        "oauth2_provider:authorize",
        query={
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "openid email",
        },
    )
    auth_response = client.get(oidc_provider_authorize_url, follow=True)

    # The redirect chain must point to the product, without going through the IdP
    assert auth_response.redirect_chain, "A redirect to the product is expected"
    final_url = auth_response.redirect_chain[-1][0]
    assert final_url.startswith(REDIRECT_URI), (
        f"The final redirect must point to the product, got: {final_url}"
    )

    # Extract the authorization code
    parsed_final = urlparse(final_url)
    final_params = parse_qs(parsed_final.query)
    assert "code" in final_params, (
        "An authorization code must be present in the redirect to the product"
    )
    authorization_code = final_params["code"][0]

    # ---- Step 2: The product exchanges the code for tokens ----
    token_response = client.post(
        "/api/v1.0/o/token/",
        {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    assert token_response.status_code == 200
    token_data = token_response.json()
    assert "access_token" in token_data
    assert "id_token" in token_data

    # No call to the upstream OIDC provider must have been made,
    # since the user already had an active session
    upstream_calls = [
        call
        for call in responses.calls
        if settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT in call.request.url
    ]
    assert len(upstream_calls) == 0, (
        "The upstream OIDC provider MUST NOT be contacted when the user already has "
        f"an active session. Detected calls: {[c.request.url for c in upstream_calls]}"
    )
