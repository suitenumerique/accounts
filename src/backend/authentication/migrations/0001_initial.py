import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import social_django.storage

import core.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IdentityProviderUser",
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
                (
                    "provider",
                    models.CharField(
                        choices=[("pro-connect", "ProConnect")],
                        verbose_name="identity provider",
                    ),
                ),
                (
                    "uid",
                    models.CharField(
                        db_index=True, verbose_name="identity provider user id"
                    ),
                ),
                (
                    "extra_data",
                    core.fields.TypeSafeEncryptedJSONField(blank=True, default=dict),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="identity_providers",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("provider", "uid"),
                        name="unique_identity_provider_uid_per_provider",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("uid", ""), _negated=True),
                        name="identity_provider_uid_required",
                    ),
                ],
            },
            bases=(models.Model, social_django.storage.DjangoUserMixin),
        ),
    ]
