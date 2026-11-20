"""Tests for the authentication system checks."""

from authentication.checks import check_login_error_url


def test_check_login_error_url_missing(settings):
    """A missing login error URL should raise a warning."""
    settings.SOCIAL_AUTH_LOGIN_ERROR_URL = None

    assert [warning.id for warning in check_login_error_url(None)] == [
        "authentication.W001"
    ]


def test_check_login_error_url_set(settings):
    """A configured login error URL should not raise any warning."""
    settings.SOCIAL_AUTH_LOGIN_ERROR_URL = "http://frontend.app/login-error/"

    assert not check_login_error_url(None)
