"""End-to-end tests for the complete OIDC logout flow."""

from urllib.parse import urljoin

from django.contrib import auth
from django.urls import reverse

import pytest
from oauth2_provider.models import (
    get_access_token_model,
    get_id_token_model,
    get_refresh_token_model,
)
from pytest_django.asserts import assertRedirects

from core.utils import state
from core.utils.urls import add_query_params, get_query_params

from authentication.backends import ProConnect
from authentication.factories import IdentityProviderUserFactory
from oidc_provider.factories import SimpleApplicationFactory
from oidc_provider.tests.test_views import _issue_tokens


@pytest.fixture(name="upstream_oidc_mocks")
def upstream_oidc_mocks_fixture(settings, responses):
    """Fixture that mock HTTP calls to an upstream OIDC Provider."""
    settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT = "http://upstream-oidc.test"
    settings.SOCIAL_AUTH_PRO_CONNECT_KEY = "idp-client-id"

    well_known = {
        "end_session_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/logout/",
    }
    responses.add(
        responses.GET,
        f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/.well-known/openid-configuration",
        json=well_known,
        status=200,
    )


@pytest.mark.usefixtures("upstream_oidc_mocks")
def test_full_oidc_logout_flow(client):
    """Verify the complete end-to-end OIDC logout flow.

    Scenario:
    1. Call account's RP-initiated endpoint.
    2. Get redirected to account's logout endpoint.
    3. Get redirected to the Identity Provider's RP-initiated endpoint.
    4. Get disconnected, and tokens revoked.
    """
    application = SimpleApplicationFactory()
    idp_user = IdentityProviderUserFactory(
        provider=ProConnect.name, extra_data={"id_token": "idp-id-token"}
    )
    id_token = _issue_tokens(client, application, idp_user.user)["id_token"]
    post_logout_redirect_uri = application.post_logout_redirect_uris.split()[0]

    # ---- Step 1: The RP-initiated logout endpoint redirect to our logout endpoint ----
    response = client.get(
        reverse(
            "oauth2_provider:rp-initiated-logout",
            query={
                "id_token_hint": id_token,
                "client_id": application.client_id,
                "post_logout_redirect_uri": post_logout_redirect_uri,
                "state": "post-logout-redirect-uri-state",
            },
        ),
    )
    state_key = get_query_params(response.url)["state"]

    authentication_logout_url = urljoin(
        "http://testserver",
        reverse("authentication:logout", query={"state": state_key, "prompt": "none"}),
    )
    assertRedirects(response, authentication_logout_url, fetch_redirect_response=False)

    # ---- Step 2: Our logout endpoint redirect to the identity provider's end session endpoint ----
    response = client.get(authentication_logout_url)

    identity_provider_logout_url = add_query_params(
        "http://upstream-oidc.test/logout/",
        {
            "id_token_hint": "idp-id-token",
            "client_id": "idp-client-id",
            "post_logout_redirect_uri": urljoin(
                "http://testserver", reverse("authentication:logout-end")
            ),
            "state": state_key,
        },
    )
    assertRedirects(
        response, identity_provider_logout_url, fetch_redirect_response=False
    )

    # ---- Step 3: The upstream identity provider calls back ----
    authentication_logout_end_url = reverse(
        "authentication:logout-end", query={"state": state_key}
    )

    response = client.get(authentication_logout_end_url)
    assertRedirects(
        response,
        add_query_params(
            post_logout_redirect_uri, {"state": "post-logout-redirect-uri-state"}
        ),
        fetch_redirect_response=False,
    )
    # Session should have be flushed
    assert auth.SESSION_KEY not in client.session
    assert state.SESSION_KEY not in client.session
    # Tokens should not be revoked
    assert get_id_token_model().objects.count() == 1
    assert get_access_token_model().objects.count() == 1
    assert get_refresh_token_model().objects.count() == 1
