"""Accounts authentication application."""

import functools

from django.apps import AppConfig
from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.utils.translation import gettext_lazy as _

from authentication import signals


class AuthenticationConfig(AppConfig):
    """Configuration class for the accounts authentication app."""

    name = "authentication"
    verbose_name = _("Accounts authentication application")

    def ready(self) -> None:
        user_login_failed.connect(
            functools.partial(
                signals.django_auth_capture_event, event_name="django:user_login_failed"
            ),
            weak=False,
        )
        user_logged_in.connect(
            functools.partial(
                signals.django_auth_capture_event, event_name="django:user_logged_in"
            ),
            weak=False,
        )
        user_logged_out.connect(
            functools.partial(
                signals.django_auth_capture_event, event_name="django:user_logged_out"
            ),
            weak=False,
        )
