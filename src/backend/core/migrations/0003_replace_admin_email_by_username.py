from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="admin_email",
        ),
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.EmailField(
                default="",
                error_messages={"unique": "A user with that username already exists."},
                max_length=254,
                unique=True,
                verbose_name="username",
            ),
            preserve_default=False,
        ),
    ]
