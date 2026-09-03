"""
Tests for authentication views.
"""

from urllib.parse import urljoin, urlparse

from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects
from rest_framework.status import (
    HTTP_302_FOUND,
)
from social_django.utils import load_strategy

from core.factories import UserFactory
from core.utils.state import set_state
from core.utils.urls import add_query_params, get_query_params

from authentication.factories import IdentityProviderUserFactory


@pytest.fixture(name="upstream_oidc_mocks")
def upstream_oidc_mocks_fixture(settings, responses, invalidate_psa_backends_cache):  # pylint: disable=unused-argument
    """Fixture that mock HTTP calls to an upstream OIDC Provider."""
    settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT = "http://upstream-oidc.test"
    settings.SOCIAL_AUTH_PRO_CONNECT_KEY = "idp-client-id"

    well_known = {
        "issuer": settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT,
        "authorization_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/authorize/",
        "end_session_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/logout/",
    }
    responses.add(
        responses.GET,
        f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/.well-known/openid-configuration",
        json=well_known,
        status=200,
    )


@pytest.mark.parametrize(
    "query,expected_next",
    [
        pytest.param(None, None, id="without_query"),
        pytest.param({}, None, id="empty_query"),
        pytest.param(
            {"next": "/path/?param=value&other=1"},
            "/path/?param=value&other=1",
            id="next_is_forwarded_and_escaped",
        ),
        pytest.param(
            {"next": "/dashboard/", "foo": "bar"},
            "/dashboard/",
            id="only_next_is_forwarded",
        ),
    ],
)
@pytest.mark.usefixtures("upstream_oidc_mocks")
def test_login_routing_view_redirect(client, query, expected_next):
    """GET on login view should redirect to OIDC authenticate endpoint."""
    response = client.get(reverse("authentication:login", query=query))
    assert response.status_code == HTTP_302_FOUND

    # Check we are redirected to the upstream OIDC Provider's authorize view
    url_parts = urlparse(response.url)
    assert url_parts.netloc == "upstream-oidc.test"
    assert url_parts.path == "/authorize/"

    # Check that the "next" query param was correctly saved
    assert load_strategy(client).session_get("next") == expected_next


@pytest.mark.usefixtures("upstream_oidc_mocks")
def test_logout_view(settings, client):
    """Test LogoutView."""
    settings.FRONTEND_LOGOUT_URL = "/frontend-logout"
    client.force_login(IdentityProviderUserFactory().user)
    state_key = set_state(client.session)

    def make_identity_provider_logout_url(state):
        return add_query_params(
            urljoin(settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT, "/logout/"),
            {
                "client_id": "idp-client-id",
                "post_logout_redirect_uri": urljoin(
                    "http://testserver", reverse("authentication:logout-end")
                ),
                "state": state,
            },
        )

    # GET request without `state` parameter -> Prompt the user
    response = client.get(reverse("authentication:logout"))
    assertRedirects(
        response, settings.FRONTEND_LOGOUT_URL, fetch_redirect_response=False
    )

    response = client.get(
        reverse("authentication:logout", query={"state": "do-not-exists"})
    )
    assertRedirects(
        response, settings.FRONTEND_LOGOUT_URL, fetch_redirect_response=False
    )

    # GET with `state` parameter -> Prompt the user based on the `prompt` parameter
    response = client.get(
        reverse(
            "authentication:logout", query={"state": state_key, "prompt": "consent"}
        )
    )
    assertRedirects(
        response,
        add_query_params(settings.FRONTEND_LOGOUT_URL, {"state": state_key}),
        fetch_redirect_response=False,
    )

    response = client.get(
        reverse("authentication:logout", query={"state": state_key, "prompt": "none"})
    )
    assertRedirects(
        response,
        make_identity_provider_logout_url(state_key),
        fetch_redirect_response=False,
    )

    response = client.get(reverse("authentication:logout", query={"state": state_key}))
    assertRedirects(
        response,
        make_identity_provider_logout_url(state_key),
        fetch_redirect_response=False,
    )

    # POST request with `state` parameter -> Redirect to IdP
    response = client.post(reverse("authentication:logout"), {"state": state_key})
    assertRedirects(
        response,
        make_identity_provider_logout_url(state_key),
        fetch_redirect_response=False,
    )

    # POST request without `state` parameter -> Create one then redirect to IdP
    response = client.post(reverse("authentication:logout"))
    assertRedirects(
        response,
        make_identity_provider_logout_url(get_query_params(response.url)["state"]),
        fetch_redirect_response=False,
    )


def test_logout_end_view_without_valid_state(settings, client):
    """GET on LogoutEndView without a valid `state` parameter should prompt the user."""
    settings.FRONTEND_LOGOUT_URL = "http://frontend.app/"
    client.force_login(UserFactory())

    response = client.get(reverse("authentication:logout-end"))
    assertRedirects(
        response, settings.FRONTEND_LOGOUT_URL, fetch_redirect_response=False
    )

    response = client.get(
        reverse("authentication:logout-end", query={"state": "do-not-exists"})
    )
    assertRedirects(
        response, settings.FRONTEND_LOGOUT_URL, fetch_redirect_response=False
    )


def test_logout_end_view_with_valid_state_without_post_logout_redirect_uri(
    settings, client
):
    """Test LogoutEndView() default redirection on success."""
    settings.LOGOUT_REDIRECT_URL = "/logout-redirect"
    client.force_login(UserFactory())

    response = client.get(
        reverse("authentication:logout-end", query={"state": set_state(client.session)})
    )
    assertRedirects(
        response, settings.LOGOUT_REDIRECT_URL, fetch_redirect_response=False
    )


def test_logout_end_view_with_valid_state_follow_post_logout_redirect_uri(client):
    """Test LogoutEndView() redirect to ``post_logout_redirect_uri`` on success."""
    client.force_login(UserFactory())
    post_logout_redirect_uri = "/post_logout_redirect_uri"

    response = client.get(
        reverse(
            "authentication:logout-end",
            query={
                "state": set_state(
                    client.session,
                    data={"post_logout_redirect_uri": post_logout_redirect_uri},
                )
            },
        )
    )
    assertRedirects(response, post_logout_redirect_uri, fetch_redirect_response=False)
