from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_uuid7_pk"),
    ]

    operations = [
        migrations.AddField(
            model_name="identityprovideruser",
            name="id_key",
            field=models.CharField(blank=True, default=""),
        ),
    ]
