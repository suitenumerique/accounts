"""
Tests for authentication views.
"""

from django.urls import reverse

import pytest
from pytest_django.asserts import assertRedirects
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

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


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_logout_view(settings, client, method):
    """Test calling our LogoutView."""
    settings.LOGOUT_REDIRECT_URL = "/example-logout"
    client.force_login(UserFactory())

    assert client.get(reverse("users-me")).status_code == HTTP_200_OK
    assertRedirects(
        getattr(client, method.lower())(reverse("authentication:logout")),
        "/example-logout",
        fetch_redirect_response=False,
    )
    # Check we are indeed log out
    assert client.get(reverse("users-me")).status_code == HTTP_403_FORBIDDEN
