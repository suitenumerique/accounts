import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_remove_user_metadata"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7,
                editable=False,
                help_text="primary key for the record as UUID",
                primary_key=True,
                serialize=False,
                verbose_name="id",
            ),
        ),
    ]
