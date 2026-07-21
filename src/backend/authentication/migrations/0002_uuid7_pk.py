import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="identityprovideruser",
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
