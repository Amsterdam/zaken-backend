from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0019_remove_gebruikersinvoer_energie_index_geldig_voor_wws"),
    ]

    operations = [
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="huurovereenkomst_afgesloten_op",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="monument_rijksmonument_extra_punten",
            field=models.DecimalField(decimal_places=2, default=50.0, max_digits=8),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="monument_rijksmonument_huurprijsopslag_factor",
            field=models.DecimalField(decimal_places=2, default=1.35, max_digits=4),
        ),
    ]
