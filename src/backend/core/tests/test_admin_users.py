"""Tests for the users admin."""

from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest

from core import factories

User = get_user_model()

pytestmark = pytest.mark.django_db


def _user_with_stored_email(email):
    """Create a user storing the email as is, like a user the migration kept."""
    user = factories.UserFactory()
    User.objects.filter(pk=user.pk).update(email=email)
    return user


def test_admin_users_email_not_normalized_filter(client):
    """The filter should only list the users whose email is not stored normalized."""
    admin_user = factories.UserFactory(is_staff=True, is_superuser=True)
    factories.UserFactory(email="marie.dupont@example.com")
    kept = _user_with_stored_email("Marie.Dupont@example.com")
    spaced = _user_with_stored_email(" john.doe@example.com")
    _user_with_stored_email("dısk@example.com")
    client.force_login(admin_user)

    response = client.get(
        reverse("admin:users_user_changelist"), {"email_status": "not_normalized"}
    )

    assert response.status_code == 200
    assert set(response.context["cl"].result_list) == {kept, spaced}
