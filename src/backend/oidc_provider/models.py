"""Models for OIDC provider."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from oauth2_provider.settings import oauth2_settings

from core.models import BaseModel


class ApplicationPolicy(BaseModel):
    """Accounts' policy for an oauth2_provider Application.

    An Application without policy uses the default values. oauth2_provider's
    Application model is swappable, and cannot be swapped once migrated.
    """

    application = models.OneToOneField(
        oauth2_settings.APPLICATION_MODEL,
        on_delete=models.CASCADE,
        related_name="accounts_policy",
        verbose_name=_("application"),
    )
    import_users = models.BooleanField(
        verbose_name=_("import users"),
        help_text=_(
            "Allow the application to import its users, creating the unknown ones. "
            "Transitional: only while the product replaces its identity provider's "
            "subs by accounts' subs."
        ),
        default=False,
    )

    class Meta:
        verbose_name = _("application policy")
        verbose_name_plural = _("application policies")

    def __str__(self):
        return str(self.application)

    @classmethod
    def for_application(cls, application):
        """Return the policy of an application, the default one if it has none."""
        policy = getattr(application, "accounts_policy", None)
        return policy or cls(application=application)
