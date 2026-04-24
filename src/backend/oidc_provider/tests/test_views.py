"""Tests for OAuth2/OIDC routes exposed under ``/o/``."""

# pylint: disable=redefined-outer-name,no-member

import base64
from urllib.parse import parse_qs, urlparse

import pytest
from oauth2_provider.models import AccessToken, Grant, RefreshToken

from core.factories import UserFactory

from oidc_provider.factories import (
    CLIENT_SECRET,
    REDIRECT_URI,
    SimpleApplicationFactory,
)

pytestmark = pytest.mark.django_db


def _build_basic_auth_headers(application):
    """Return HTTP Basic Auth headers for the OAuth2 client."""
    credentials = f"{application.client_id}:{CLIENT_SECRET}".encode()
    encoded_credentials = base64.b64encode(credentials).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {encoded_credentials}"}


def _build_authorize_params(application, **overrides):
    """Return a default authorization request payload."""
    params = {
        "response_type": "code",
        "client_id": application.client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid email",
        "state": "test-state",
    }
    params.update(overrides)
    return params


def _get_redirect_params(response):
    """Extract query parameters from a redirect response."""
    return parse_qs(urlparse(response["Location"]).query)


def _authorize(client, application, user, **overrides):
    """Perform an authorization request for a logged-in user."""
    client.force_login(user)
    return client.get(
        "/o/authorize/", _build_authorize_params(application, **overrides)
    )


def _get_authorization_code(client, application, user, **overrides):
    """Issue an authorization code and return it."""
    response = _authorize(client, application, user, **overrides)

    assert response.status_code == 302
    assert response["Location"].startswith(REDIRECT_URI)

    params = _get_redirect_params(response)
    assert "code" in params
    return params["code"][0]


def _exchange_code(client, application, code, **overrides):
    """Exchange an authorization code for tokens."""
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": application.client_id,
        "client_secret": CLIENT_SECRET,
    }
    payload.update(overrides)
    return client.post("/o/token/", payload)


def _issue_tokens(client, application, user):
    """Go through the authorization code flow and return the token response payload."""
    code = _get_authorization_code(client, application, user)
    response = _exchange_code(client, application, code)

    assert response.status_code == 200
    return response.json()


def test_authorize_redirects_anonymous_user_to_login(client):
    """Anonymous users should be redirected to the login flow."""
    application = SimpleApplicationFactory()
    response = client.get("/o/authorize/", _build_authorize_params(application))

    assert response.status_code == 302
    assert (
        "/login/" in response["Location"]
        or "/oidc/authenticate/" in response["Location"]
    )


def test_authorize_with_prompt_none_redirects_with_login_required_error(
    client,
):
    """An anonymous silent authorization request should redirect with ``login_required``."""
    application = SimpleApplicationFactory()
    response = client.get(
        "/o/authorize/",
        _build_authorize_params(application, prompt="none", state="silent-state"),
    )

    assert response.status_code == 302
    assert response["Location"].startswith(REDIRECT_URI)

    params = _get_redirect_params(response)
    assert params["error"] == ["login_required"]
    assert params["state"] == ["silent-state"]


def test_authorize_returns_authorization_code_for_authenticated_user(
    client,
):
    """A logged-in user should receive an authorization code and the original state."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    response = _authorize(client, application, user, state="roundtrip-state")

    assert response.status_code == 302
    assert response["Location"].startswith(REDIRECT_URI)

    params = _get_redirect_params(response)
    code = params["code"][0]

    assert params["state"] == ["roundtrip-state"]
    assert Grant.objects.filter(code=code, application=application, user=user).exists()


def test_authorize_rejects_unknown_client_id(client):
    """An authorization request for an unknown client must fail early."""
    user = UserFactory()
    client.force_login(user)

    response = client.get(
        "/o/authorize/",
        {
            "response_type": "code",
            "client_id": "missing-client",
            "redirect_uri": REDIRECT_URI,
            "scope": "openid email",
        },
    )

    assert response.status_code == 400
    assert not response.has_header("Location")


def test_authorize_rejects_non_registered_redirect_uri(client):
    """The client must not be able to use a redirect URI that is not registered."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    response = _authorize(
        client,
        application,
        user,
        redirect_uri="https://attacker.example.test/callback",
    )

    assert response.status_code == 400
    assert not response.has_header("Location")


def test_token_exchanges_authorization_code_for_tokens(client):
    """A valid authorization code exchange should issue the expected tokens."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    code = _get_authorization_code(client, application, user)

    response = _exchange_code(client, application, code)

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "Bearer"
    assert payload["scope"] == "openid email"
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert "id_token" in payload


def test_token_rejects_reused_authorization_code(client):
    """Authorization codes are single-use and must be rejected once consumed."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    code = _get_authorization_code(client, application, user)

    first_response = _exchange_code(client, application, code)
    second_response = _exchange_code(client, application, code)

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["error"] == "invalid_grant"


def test_token_rejects_invalid_client_secret(client):
    """A confidential client must authenticate with the correct secret."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    code = _get_authorization_code(client, application, user)

    response = _exchange_code(
        client,
        application,
        code,
        client_secret="wrong-secret",
    )

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"


def test_token_rejects_mismatched_redirect_uri(client):
    """The redirect URI used at token exchange must match the authorization request."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    code = _get_authorization_code(client, application, user)

    response = _exchange_code(
        client,
        application,
        code,
        redirect_uri="https://other.example.test/callback",
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_token_rejects_unsupported_grant_type(client):
    """Unsupported grant types should return the RFC-compliant error."""
    application = SimpleApplicationFactory()
    response = client.post(
        "/o/token/",
        {
            "grant_type": "implicit",
            "client_id": application.client_id,
            "client_secret": CLIENT_SECRET,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "unsupported_grant_type"


def test_revoke_token_revokes_access_tokens(client):
    """Revoking an access token should delete it from the persistence layer."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    tokens = _issue_tokens(client, application, user)
    access_token = tokens["access_token"]

    response = client.post(
        "/o/revoke_token/",
        {"token": access_token, "token_type_hint": "access_token"},
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 200
    assert not AccessToken.objects.filter(token=access_token).exists()


def test_revoke_token_revokes_refresh_tokens_and_linked_access_token(
    client,
):
    """Revoking a refresh token should also revoke the access token it issued."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    tokens = _issue_tokens(client, application, user)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    response = client.post(
        "/o/revoke_token/",
        {"token": refresh_token, "token_type_hint": "refresh_token"},
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 200
    assert not AccessToken.objects.filter(token=access_token).exists()
    assert RefreshToken.objects.get(token=refresh_token).revoked is not None


def test_revoke_token_is_idempotent_for_unknown_tokens(client):
    """Revoking an unknown token should still succeed to avoid leaking token validity."""
    application = SimpleApplicationFactory()
    response = client.post(
        "/o/revoke_token/",
        {"token": "missing-token", "token_type_hint": "access_token"},
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 200
    assert response.content == b""


def test_revoke_token_rejects_unauthenticated_clients(client):
    """The revocation endpoint must reject requests without client authentication."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    tokens = _issue_tokens(client, application, user)

    response = client.post(
        "/o/revoke_token/",
        {"token": tokens["access_token"], "token_type_hint": "access_token"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"


def test_introspect_returns_active_metadata_for_valid_access_token(
    client,
):
    """A valid access token should be reported as active with its metadata."""
    application = SimpleApplicationFactory()
    user = UserFactory(email="test@example.com", sub="123")
    tokens = _issue_tokens(client, application, user)

    response = client.post(
        "/o/introspect/",
        {"token": tokens["access_token"]},
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload.pop("exp"), int)  # might check the value at some point
    assert payload == {
        "active": True,
        "iss": "http://testserver/o",
        "scope": "openid email",
        "client_id": application.client_id,
        "email": "test@example.com",
        "sub": "123",
    }


def test_introspect_returns_inactive_for_unknown_token(client):
    """Unknown tokens should be reported as inactive."""
    application = SimpleApplicationFactory()
    response = client.get(
        "/o/introspect/",
        {"token": "missing-token"},
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 200
    assert response.json() == {"active": False}


def test_introspect_returns_inactive_for_revoked_access_token(
    client,
):
    """A revoked token should no longer be reported as active."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    tokens = _issue_tokens(client, application, user)
    access_token = tokens["access_token"]

    client.post(
        "/o/revoke_token/",
        {"token": access_token, "token_type_hint": "access_token"},
        **_build_basic_auth_headers(application),
    )

    response = client.get(
        "/o/introspect/",
        {"token": access_token},
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 200
    assert response.json() == {"active": False}


def test_introspect_rejects_unauthenticated_clients(client):
    """The introspection endpoint must reject requests without client authentication."""
    application = SimpleApplicationFactory()
    user = UserFactory()
    tokens = _issue_tokens(client, application, user)

    response = client.post("/o/introspect/", {"token": tokens["access_token"]})

    assert response.status_code == 403
