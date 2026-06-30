"""Accounts Users application"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """Configuration class for the accounts users app."""

    name = "users"
    app_label = "users"
    verbose_name = _("Accounts users application")
