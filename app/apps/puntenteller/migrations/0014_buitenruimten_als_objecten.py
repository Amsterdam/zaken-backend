import apps.puntenteller.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0013_woonvoorzieningen_handicap"),
    ]

    operations = [
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="buitenruimten",
            field=models.JSONField(
                blank=True,
                default=apps.puntenteller.models.default_extra_ruimten,
            ),
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="buitenruimte_gemeenschappelijke_buitenruimte",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="buitenruimte_prive_buitenruimte",
        ),
        migrations.AddField(
            model_name="kengetal",
            name="buitenruimte_gemeenschappelijke_punten_per_m2",
            field=models.DecimalField(decimal_places=2, default=0.75, max_digits=8),
        ),
        migrations.RenameField(
            model_name="kengetal",
            old_name="buitenruimte_geen_gemeenschappelijke_aftrek",
            new_name="buitenruimte_geen_buitenruimte_aftrek",
        ),
        migrations.AddField(
            model_name="kengetal",
            name="buitenruimte_max_punten",
            field=models.DecimalField(decimal_places=2, default=15.0, max_digits=8),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="buitenruimte_prive_basispunten",
            field=models.DecimalField(decimal_places=2, default=2.0, max_digits=8),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="buitenruimte_prive_punten_per_m2",
            field=models.DecimalField(decimal_places=2, default=0.35, max_digits=8),
        ),
        migrations.RemoveField(
            model_name="kengetal",
            name="buitenruimte_gemeenschappelijke_buitenruimte_factor",
        ),
        migrations.RemoveField(
            model_name="kengetal",
            name="buitenruimte_prive_buitenruimte_factor",
        ),
    ]
