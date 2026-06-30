from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="full_name",
            field=models.CharField(
                blank=True, default="", max_length=100, verbose_name="full name"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="short_name",
            field=models.CharField(
                blank=True, default="", max_length=100, verbose_name="short name"
            ),
        ),
    ]
