from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0012_rename_toiletruimte_sanitair_kengetallen"),
    ]

    operations = [
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="woonvoorziening_handicap",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="woonvoorziening_handicap_netto_investering",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="woonvoorziening_handicap_bedrag_per_punt",
            field=models.DecimalField(decimal_places=2, default=332.0, max_digits=8),
        ),
    ]
