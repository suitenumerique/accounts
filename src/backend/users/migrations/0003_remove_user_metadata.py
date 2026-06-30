from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_non_nullable_full_name_and_short_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="metadata",
        ),
    ]
