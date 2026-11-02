import logging

from django.db import migrations
from django.db.models import F

from core.utils.emails import normalize_email

logger = logging.getLogger(__name__)


def forward(apps, schema_editor):
    User = apps.get_model("users", "User")

    # An already normalized email stays with its user. Otherwise, the last logged in
    # user wins a shared normalized email, then the oldest one.
    # Not by id: users created before `0004_uuid7_pk` have random ids.
    users = list(
        User.objects.order_by(
            F("last_login").desc(nulls_last=True), "created_at", "id"
        ).values_list("id", "email")
    )
    user_ids_by_email = {
        email: user_id for user_id, email in users if normalize_email(email) == email
    }

    to_update = []
    for user_id, email in users:
        normalized = normalize_email(email)
        if normalized == email:
            continue
        # Emails are unique: a user whose normalized email is already taken keeps
        # its email, to be handled by hand.
        if other_user_id := user_ids_by_email.get(normalized):
            logger.error(
                "Email of user %s not normalized, already used by user %s",
                user_id,
                other_user_id,
            )
            continue
        user_ids_by_email[normalized] = user_id
        to_update.append(User(id=user_id, email=normalized))

    User.objects.bulk_update(to_update, ["email"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_accounts_sub"),
    ]

    operations = [
        migrations.RunPython(
            forward, reverse_code=migrations.RunPython.noop, elidable=True
        ),
    ]
