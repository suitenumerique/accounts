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
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.test import Client

import pytest
import responses

from core.authentication.backends import OIDCAuthenticationBackend
from core.factories import UserFactory
from core.models import User

from oidc_provider.factories import (
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    SimpleApplicationFactory,
)

pytestmark = pytest.mark.django_db


UPSTREAM_OIDC_ISSUER = "http://upstream-oidc.test"
UPSTREAM_TOKEN_ENDPOINT = f"{UPSTREAM_OIDC_ISSUER}/token"
UPSTREAM_USERINFO_ENDPOINT = f"{UPSTREAM_OIDC_ISSUER}/userinfo"
UPSTREAM_JWKS_ENDPOINT = f"{UPSTREAM_OIDC_ISSUER}/jwks"


def _build_authorization_url():
    """Return the authorization URL that the product would send to the browser."""
    return (
        "/o/authorize/"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid+email"
    )


def _register_upstream_oidc_mocks(
    sub="test-user-sub-123",
    email="testuser@example.com",
    first_name="Test",
    last_name="User",
):
    """
    Register mocks for the upstream OIDC provider (token + userinfo endpoints).

    Returns the sub used, to facilitate assertions.
    """
    responses.add(
        responses.POST,
        re.compile(re.escape(UPSTREAM_TOKEN_ENDPOINT)),
        json={
            "access_token": "upstream-access-token",
            "id_token": "upstream-id-token",
            "refresh_token": "upstream-refresh-token",
            "token_type": "Bearer",
        },
        status=200,
    )
    responses.add(
        responses.GET,
        re.compile(re.escape(UPSTREAM_USERINFO_ENDPOINT)),
        json={
            "sub": sub,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        },
        status=200,
    )
    return sub


@pytest.fixture(name="upstream_oidc_settings")
def fixture_upstream_oidc_settings(settings):
    """Settings for upstream OIDC provider (token + userinfo endpoints)."""
    settings.OIDC_OP_TOKEN_ENDPOINT = UPSTREAM_TOKEN_ENDPOINT
    settings.OIDC_OP_USER_ENDPOINT = UPSTREAM_USERINFO_ENDPOINT
    settings.OIDC_OP_JWKS_ENDPOINT = UPSTREAM_JWKS_ENDPOINT
    settings.OIDC_OP_AUTHORIZATION_ENDPOINT = f"{UPSTREAM_OIDC_ISSUER}/authorize"
    settings.OIDC_RP_CLIENT_ID = "accounts-rp"
    settings.OIDC_RP_CLIENT_SECRET = "accounts-rp-secret"
    settings.LOGIN_REDIRECT_URL = "/"


@responses.activate
def test_full_oidc_auth_flow_new_user(upstream_oidc_settings):  # pylint: disable=too-many-locals,unused-argument
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

    # Register upstream OIDC provider mocks
    sub = _register_upstream_oidc_mocks()

    client = Client()

    # ---- Step 1: The product sends the user to Accounts's authorization endpoint ----
    response = client.get(_build_authorization_url())

    # Accounts must redirect to /login/ because the user is not authenticated
    assert response.status_code == 302
    location = response["Location"]
    assert "/login/" in location or "/oidc/authenticate/" in location

    # Follow the redirect chain up to the upstream OIDC provider
    # We follow redirects manually to intercept the external URL
    response = client.get(response["Location"], follow=False)
    # May require several hops (login -> oidc/authenticate -> external IdP)
    max_hops = 5
    hops = 0
    while response.status_code == 302 and hops < max_hops:
        next_location = response["Location"]
        # Stop when the URL points to the external OIDC provider
        if next_location.startswith(UPSTREAM_OIDC_ISSUER):
            break
        response = client.get(next_location, follow=False)
        hops += 1

    # We must have been redirected to the upstream OIDC provider
    assert response.status_code == 302
    idp_redirect_url = response["Location"]
    assert idp_redirect_url.startswith(UPSTREAM_OIDC_ISSUER)

    # Extract the `state` from the redirect URL to the IdP
    parsed = urlparse(idp_redirect_url)
    params = parse_qs(parsed.query)
    state = params["state"][0]

    # ---- Step 2: The IdP calls back Accounts with an authorization code ----
    # Mock verify_token to avoid signing a real JWT
    def mock_verify_token(self, token, *args, **kwargs):  # pylint: disable=unused-argument
        """Mock of verify_token returning claims without signature verification."""
        return {
            "sub": sub,
            "email": "testuser@example.com",
        }

    with patch.object(OIDCAuthenticationBackend, "verify_token", mock_verify_token):
        callback_response = client.get(
            "/oidc/callback/",
            {"code": "upstream-auth-code", "state": state},
            follow=False,
        )

    # Accounts must redirect after successful authentication
    assert callback_response.status_code in (302, 200)

    # The user must now be authenticated in the session
    assert User.objects.filter(sub=sub).exists(), (
        "The user must have been created after OIDC authentication"
    )

    # Follow the post-login redirect chain until we find the redirect to the product
    if callback_response.status_code == 302:
        follow_response = client.get(callback_response["Location"], follow=True)
        # The last redirect must point to the product
        final_url = (
            follow_response.redirect_chain[-1][0]
            if follow_response.redirect_chain
            else ""
        )
        if not final_url.startswith(REDIRECT_URI):
            # OAuth2 authorization may not have happened yet;
            # re-issue the authorization request now that the user is logged in
            auth_response = client.get(_build_authorization_url(), follow=True)
            final_url = (
                auth_response.redirect_chain[-1][0]
                if auth_response.redirect_chain
                else ""
            )
    else:
        auth_response = client.get(_build_authorization_url(), follow=True)
        final_url = (
            auth_response.redirect_chain[-1][0] if auth_response.redirect_chain else ""
        )

    assert final_url.startswith(REDIRECT_URI), (
        f"The final redirect must point to the product, got: {final_url}"
    )

    # Extract the authorization code returned to the product
    parsed_final = urlparse(final_url)
    final_params = parse_qs(parsed_final.query)
    assert "code" in final_params, (
        "An authorization code must be present in the redirect to the product"
    )
    authorization_code = final_params["code"][0]

    # ---- Step 3: The product exchanges the code for tokens ----
    token_response = client.post(
        "/o/token/",
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

    # Verify that the upstream OIDC provider was contacted (token + userinfo)
    upstream_calls = [
        call for call in responses.calls if UPSTREAM_OIDC_ISSUER in call.request.url
    ]
    assert len(upstream_calls) >= 1, (
        "The upstream OIDC provider must have been contacted at least once"
    )


@responses.activate
def test_oidc_auth_flow_existing_session_no_upstream_call(upstream_oidc_settings):  # pylint: disable=unused-argument
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

    client = Client()
    client.force_login(user)

    # ---- Step 1: The product sends the user to Accounts's authorization endpoint ----
    # The user is already logged in; Accounts must grant authorization directly
    auth_response = client.get(_build_authorization_url(), follow=True)

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
        "/o/token/",
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
        call for call in responses.calls if UPSTREAM_OIDC_ISSUER in call.request.url
    ]
    assert len(upstream_calls) == 0, (
        "The upstream OIDC provider MUST NOT be contacted when the user already has "
        f"an active session. Detected calls: {[c.request.url for c in upstream_calls]}"
    )
