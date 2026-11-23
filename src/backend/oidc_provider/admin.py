"""Admin classes and registrations for the OIDC provider app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from oauth2_provider.admin import ApplicationAdmin as OAuth2ApplicationAdmin
from oauth2_provider.models import get_application_model

from oidc_provider.models import ApplicationPolicy


class ApplicationPolicyInline(admin.StackedInline):
    """Accounts' policy for an application."""

    model = ApplicationPolicy
    can_delete = False
    fields = ("import_users",)


class ApplicationAdmin(OAuth2ApplicationAdmin):
    """oauth2_provider's Application admin, with the accounts' policy."""

    inlines = [ApplicationPolicyInline]
    list_display = (*OAuth2ApplicationAdmin.list_display, "import_users")
    list_select_related = ("user", "accounts_policy")

    @admin.display(description=_("import users"), boolean=True)
    def import_users(self, obj):
        """Return whether the application may import its users."""
        return ApplicationPolicy.for_application(obj).import_users


# Importing oauth2_provider.admin above registered its own Application admin
admin.site.unregister(get_application_model())
admin.site.register(get_application_model(), ApplicationAdmin)
