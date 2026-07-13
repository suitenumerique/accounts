"""Accounts authentication application."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthenticationConfig(AppConfig):
    """Configuration class for the accounts authentication app."""

    name = "authentication"
    verbose_name = _("Accounts authentication application")
