"""Admin classes and registrations for core app."""

import string

from django.contrib import admin
from django.db.models import F, Func, Value
from django.db.models.functions import Trim
from django.utils.translation import gettext_lazy as _

from core import admin as core_admin

from authentication.admin import IdentityProviderUserInline

from . import models

USER_FIELDS_NOT_IMPLEMENTED = {"admin_email"}


def normalized_email():
    """Database counterpart of `core.utils.emails.normalize_email`."""
    return Trim(
        Func(
            F("email"),
            Value(string.ascii_uppercase),
            Value(string.ascii_lowercase),
            function="TRANSLATE",
        )
    )


class NotNormalizedEmailFilter(admin.SimpleListFilter):
    """Filter the users whose email is not stored normalized.

    Saving a user normalizes its email, so these are the users the migration kept
    because their normalized email belongs to another user.
    """

    title = _("email status")
    parameter_name = "email_status"

    def lookups(self, request, model_admin):
        """Return the filter options."""
        return [("not_normalized", _("Not normalized"))]

    def queryset(self, request, queryset):
        """Keep the users whose email differs from its normalized form."""
        if self.value() != "not_normalized":
            return queryset
        return queryset.annotate(normalized_email=normalized_email()).exclude(
            email=F("normalized_email")
        )


@admin.register(models.User)
class UserAdmin(core_admin.UserAdmin):
    """Admin class for the User model"""

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "sub",
                    "email",
                    "password",
                )
            },
        ),
        (
            _("Personal info"),
            {
                "fields": (
                    "full_name",
                    "short_name",
                    "language",
                    "timezone",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_device",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("created_at", "updated_at")}),
    )
    inlines = (IdentityProviderUserInline,)
    list_display = tuple(
        f
        for f in core_admin.UserAdmin.list_display
        if f not in USER_FIELDS_NOT_IMPLEMENTED
    )
    list_filter = (*core_admin.UserAdmin.list_filter, NotNormalizedEmailFilter)
    search_fields = tuple(
        f
        for f in core_admin.UserAdmin.search_fields
        if f not in USER_FIELDS_NOT_IMPLEMENTED
    )
