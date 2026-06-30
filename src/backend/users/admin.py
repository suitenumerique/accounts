"""Admin classes and registrations for core app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core import admin as core_admin

from . import models

USER_FIELDS_NOT_IMPLEMENTED = {"admin_email"}


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
    list_display = tuple(
        f
        for f in core_admin.UserAdmin.list_display
        if f not in USER_FIELDS_NOT_IMPLEMENTED
    )
    search_fields = tuple(
        f
        for f in core_admin.UserAdmin.search_fields
        if f not in USER_FIELDS_NOT_IMPLEMENTED
    )
