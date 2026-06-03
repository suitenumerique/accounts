from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthenticationConfig(AppConfig):
    name = "authentication"
    app_label = "authentication"
    verbose_name = _("Accounts authentication application")
