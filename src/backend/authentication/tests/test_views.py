"""
Tests for authentication views.
"""

from django.test import Client

import pytest

pytestmark = pytest.mark.django_db


def test_login_routing_view_redirect_to_oidc():
    """GET on login view should redirect to OIDC authenticate endpoint."""
    client = Client()
    response = client.get("/login/")

    assert response.status_code == 302
    assert response["Location"] == "/oidc/authenticate/"


def test_login_routing_view_redirect_with_next_parameter():
    """GET on login view with a 'next' parameter should encode it and pass it along."""
    client = Client()
    response = client.get("/login/", {"next": "/dashboard/"})

    assert response.status_code == 302
    assert response["Location"] == "/oidc/authenticate/?next=%2Fdashboard%2F"


def test_login_routing_view_redirect_with_next_special_characters():
    """GET on login view with special characters in 'next' should be properly encoded."""
    client = Client()
    response = client.get("/login/", {"next": "/path/?param=value&other=1"})

    assert response.status_code == 302
    location = response["Location"]
    assert location.startswith("/oidc/authenticate/?next=")
    assert "/path/" not in location.split("?next=")[1]  # Should be encoded


def test_login_routing_view_get_no_next():
    """GET without 'next' parameter should redirect to /oidc/authenticate/ without query string."""
    client = Client()
    response = client.get("/login/")

    assert response.status_code == 302
    assert "next" not in response["Location"]
