"""System checks for the authentication application."""

from django.conf import settings
from django.core.checks import Warning as CheckWarning
from django.core.checks import register


@register()
def check_login_error_url(app_configs, **kwargs):  # pylint: disable=unused-argument
    """Warn when identity provider errors would end up as a 500 error."""
    if settings.SOCIAL_AUTH_LOGIN_ERROR_URL:
        return []

    return [
        CheckWarning(
            "FRONTEND_LOGIN_ERROR_URL is not set: identity provider errors will "
            "raise a 500 error instead of redirecting to the login error page.",
            hint="Set FRONTEND_LOGIN_ERROR_URL to the frontend /login-error/ page.",
            id="authentication.W001",
        )
    ]
