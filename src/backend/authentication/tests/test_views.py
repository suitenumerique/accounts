"""
Tests for authentication views.
"""

from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects
from rest_framework.status import (
    HTTP_403_FORBIDDEN,
    HTTP_405_METHOD_NOT_ALLOWED,
)

from core.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "query,expected_query",
    [
        pytest.param(None, None, id="without_query"),
        pytest.param({}, {}, id="empty_query"),
        pytest.param(
            {"next": "/path/?param=value&other=1"},
            {"next": "/path/?param=value&other=1"},
            id="next_is_forwarded_and_escaped",
        ),
        pytest.param(
            {"next": "/dashboard/", "foo": "bar"},
            {"next": "/dashboard/"},
            id="only_next_is_forwarded",
        ),
    ],
)
def test_login_routing_view_redirect(client, query, expected_query):
    """GET on login view should redirect to OIDC authenticate endpoint."""
    response = client.get(reverse("authentication:login", query=query))

    assertRedirects(
        response,
        reverse(
            "authentication:social:begin",
            kwargs={"backend": "pro-connect"},
            query=expected_query,
        ),
        fetch_redirect_response=False,
    )


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
