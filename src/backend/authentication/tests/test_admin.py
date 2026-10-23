"""Tests for the Django admin login."""

from django.urls import reverse


def test_admin_login_with_wrong_password_does_not_crash(client):
    """A failed login on the Django admin must display the form, not a 500 error."""
    response = client.post(
        reverse("admin:login"),
        {"username": "unknown@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
