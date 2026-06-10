import django.contrib.auth.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_replace_admin_email_by_username"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RemoveField(
            model_name="user",
            name="metadata",
        ),
        migrations.RemoveField(
            model_name="user",
            name="sub",
        ),
    ]
