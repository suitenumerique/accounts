import uuid

from django.db import migrations, models

import core.validators


def forward(apps, schema_editor):
    User = apps.get_model("users", "User")

    for user in User.objects.all():
        user.sub = uuid.uuid4()
        user.save(update_fields={"sub"})


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_uuid7_pk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="sub",
            field=models.CharField(
                default=uuid.uuid4,
                help_text="Required. 255 characters or fewer. ASCII characters only.",
                max_length=255,
                unique=True,
                validators=[
                    core.validators.sub_validator,
                    core.validators.uuid_validator,
                ],
                verbose_name="sub",
            ),
        ),
        migrations.RunPython(
            forward, reverse_code=migrations.RunPython.noop, elidable=True
        ),
    ]
