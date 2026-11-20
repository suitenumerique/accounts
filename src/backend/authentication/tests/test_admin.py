"""Tests for the Django admin login."""

from django.contrib import admin
from django.urls import reverse

from social_django.models import Association


def test_admin_login_with_wrong_password_does_not_crash(client):
    """A failed login on the Django admin must display the form, not a 500 error."""
    response = client.post(
        reverse("admin:login"),
        {"username": "unknown@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 200
    assert response.context["form"].non_field_errors()


def test_association_admin_has_no_assoc_type_filter():
    """The association admin must not filter on `assoc_type`, which holds OIDC states."""
    assert admin.site.get_model_admin(Association).list_filter == ()
