"""Admin classes and registrations for the authentication app."""

import json

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from social_core.backends.utils import get_backend
from social_core.exceptions import AuthConfigurationError

from core.admin import ReadOnlyAdminMixin

from authentication.models import IdentityProviderUser

SECRET_EXTRA_DATA_KEYS = {"access_token", "id_token", "refresh_token"}


def _get_extra_data_key(entry) -> str:
    """Return the `extra_data` key of an `EXTRA_DATA` entry: `name` or `(name, alias, ...)`."""
    if isinstance(entry, str):
        return entry
    return entry[1] if len(entry) > 1 else entry[0]


def get_displayed_claims(identity_provider: IdentityProviderUser) -> dict:
    """Return the claims stored for an identity provider, without its tokens.

    Only the keys declared in the backend `EXTRA_DATA` are returned, so a value
    stored by the backend itself (tokens, timestamps...) is never displayed.
    """
    try:
        backend = get_backend(
            settings.AUTHENTICATION_BACKENDS, identity_provider.provider
        )
    except AuthConfigurationError:
        return {}

    claim_names = {
        _get_extra_data_key(entry) for entry in backend.EXTRA_DATA or []
    } - SECRET_EXTRA_DATA_KEYS
    return {
        name: value
        for name, value in identity_provider.extra_data.items()
        if name in claim_names
    }


class IdentityProviderUserClaimsMixin:
    """Display the identity provider claims, which are specific to each backend."""

    @admin.display(description=_("claims"))
    def claims(self, obj):
        """Return the stored claims, as indented JSON."""
        return format_html(
            "<pre>{}</pre>",
            json.dumps(
                get_displayed_claims(obj), indent=2, sort_keys=True, ensure_ascii=False
            ),
        )


class IdentityProviderUserInline(
    ReadOnlyAdminMixin, IdentityProviderUserClaimsMixin, admin.StackedInline
):
    """Read-only inline of the identity providers of a user."""

    model = IdentityProviderUser
    fields = ("claims", "updated_at")
    extra = 0
    can_delete = False
    show_change_link = True


@admin.register(IdentityProviderUser)
class IdentityProviderUserAdmin(
    ReadOnlyAdminMixin, IdentityProviderUserClaimsMixin, admin.ModelAdmin
):
    """Read-only admin of the identity providers associations."""

    list_display = ("user", "provider", "uid", "updated_at")
    list_filter = ("provider",)
    list_select_related = ("user",)
    ordering = ("-updated_at",)
    search_fields = ("uid", "user__email", "user__sub")
    fields = ("user", "provider", "uid", "claims", "created_at", "updated_at")
