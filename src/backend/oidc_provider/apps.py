"""Accounts OIDC Provider application."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from oauth2_provider.signals import app_authorized

from oidc_provider import signals


class OIDCProviderConfig(AppConfig):
    """Configuration class for the accounts OIDC Provider app."""

    name = "oidc_provider"
    verbose_name = _("Accounts OIDC Provider application")

    def ready(self) -> None:
        app_authorized.connect(signals.app_authorized_capture_event)
