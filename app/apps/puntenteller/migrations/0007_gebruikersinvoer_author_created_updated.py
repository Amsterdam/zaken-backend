import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0006_alter_gebruikersinvoer_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="gebruikersinvoer",
            old_name="gebruiker",
            new_name="author",
        ),
        migrations.AlterModelOptions(
            name="gebruikersinvoer",
            options={
                "ordering": ["-created", "-id"],
                "verbose_name": "gebruikersinvoer",
                "verbose_name_plural": "gebruikersinvoer",
            },
        ),
        # Bestaande rijen krijgen eenmalig het moment van migreren.
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
