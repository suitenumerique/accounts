"""
Tests for authentication views.
"""

from urllib.parse import urlparse

from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects
from rest_framework.status import (
    HTTP_302_FOUND,
    HTTP_403_FORBIDDEN,
    HTTP_405_METHOD_NOT_ALLOWED,
)
from social_django.utils import load_strategy

from core.factories import UserFactory


@pytest.fixture(name="upstream_oidc_mocks")
def upstream_oidc_mocks_fixture(settings, responses):
    """Fixture that mock HTTP calls to an upstream OIDC Provider."""
    settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT = "http://upstream-oidc.test"

    well_known = {
        "issuer": settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT,
        "authorization_endpoint": f"{settings.SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT}/authorize/",
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


def test_logout_view(settings, client):
    """Test calling the LogoutView."""
    settings.LOGOUT_REDIRECT_URL = "/example-logout"
    logout_url = reverse("authentication:logout")
    login_required_url = reverse("users-me")
    client.force_login(UserFactory())

    # With a GET request we get an error
    response = client.get(logout_url)
    assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED

    # with a POST request we should be log out
    response = client.post(logout_url)
    assertRedirects(response, "/example-logout", fetch_redirect_response=False)
    assert client.get(login_required_url).status_code == HTTP_403_FORBIDDEN
