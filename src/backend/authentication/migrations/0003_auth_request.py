import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import core.validators

import authentication.models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_uuid7_pk"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid7,
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
                ("email", models.EmailField(blank=True, max_length=254)),
                (
                    "expires_at",
                    models.DateTimeField(
                        default=authentication.models.auth_request_default_expiration,
                        editable=False,
                        help_text="date and time at which the authentication request will expire",
                        verbose_name="expiration timestamp",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="login_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AuthRequestAttempt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid7,
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
                (
                    "strategy",
                    models.CharField(
                        choices=[
                            ("PASSWORD", "through its password"),
                            ("DEVICE", "through another device"),
                        ],
                        verbose_name="authentication request strategy",
                    ),
                ),
                (
                    "client_challenge",
                    models.CharField(
                        blank=True,
                        validators=[core.validators.pkce_code_challenge_validator],
                        verbose_name="client challenge (PKCE-like)",
                    ),
                ),
                ("secret", models.CharField(blank=True)),
                (
                    "fulfilled_at",
                    models.DateTimeField(
                        default=None,
                        editable=False,
                        help_text="date and time at which the attempt was fulfilled",
                        null=True,
                        verbose_name="fulfillment timestamp",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        default=authentication.models.auth_request_default_expiration,
                        editable=False,
                        help_text="date and time at which the authentication request attempt will expire",
                        verbose_name="expiration timestamp",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="authentication.authrequest",
                        verbose_name="authentication request",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="authrequest",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(models.Q(("email", ""), _negated=True), ("user", None)),
                    models.Q(("email", ""), ("user__isnull", False)),
                    _connector="OR",
                ),
                name="email_or_user",
            ),
        ),
    ]
