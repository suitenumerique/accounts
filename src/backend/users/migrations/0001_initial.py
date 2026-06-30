import uuid

from django.db import migrations, models

import timezone_field.fields

import core.validators

import users.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="primary key for the record as UUID",
                        primary_key=True,
                        serialize=False,
                        verbose_name="id",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="date and time at which a record was created",
                        verbose_name="created on",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="date and time at which a record was last updated",
                        verbose_name="updated on",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "sub",
                    models.CharField(
                        blank=True,
                        help_text="Required. 255 characters or fewer. ASCII characters only.",
                        max_length=255,
                        null=True,
                        unique=True,
                        validators=[core.validators.sub_validator],
                        verbose_name="sub",
                    ),
                ),
                (
                    "full_name",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="full name"
                    ),
                ),
                (
                    "short_name",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="short name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="email address"
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("en-us", "English"),
                            ("fr-fr", "Français"),
                            ("de-de", "Deutsch"),
                            ("nl-nl", "Nederlands"),
                        ],
                        default=None,
                        help_text="The language in which the user wants to see the interface.",
                        max_length=10,
                        null=True,
                        verbose_name="language",
                    ),
                ),
                (
                    "timezone",
                    timezone_field.fields.TimeZoneField(
                        choices_display="WITH_GMT_OFFSET",
                        default="UTC",
                        help_text="The timezone in which the user wants to see times.",
                        use_pytz=False,
                    ),
                ),
                (
                    "is_device",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the user is a device or a real user.",
                        verbose_name="device",
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional information about the user.",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "db_table": "accounts_user",
            },
            managers=[
                ("objects", users.models.UserManager()),
            ],
        ),
    ]
