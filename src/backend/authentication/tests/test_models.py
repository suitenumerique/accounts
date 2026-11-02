"""Tests for the authentication models."""

from core import factories

from authentication.models import IdentityProviderUser


def test_get_users_by_email_email_matching():
    """Users should be found by email ignoring ASCII case only."""
    user = factories.UserFactory(email="disk@example.com")

    def get_users(email):
        return list(IdentityProviderUser.get_users_by_email(email))

    assert get_users("disk@example.com") == [user]
    assert get_users("DISK@EXAMPLE.COM") == [user]
    assert get_users("dısk@example.com") == []
    assert get_users("diſk@example.com") == []
    assert get_users("disK@example.com") == []


def test_get_users_by_email_skips_inactive():
    """Inactive users should not be found by email."""
    factories.UserFactory(email="disk@example.com", is_active=False)

    assert not IdentityProviderUser.get_users_by_email("disk@example.com").exists()
