from django.db import migrations, models


class Migration(migrations.Migration):
    # Beleidsboek 2.12.2: aanbelfunctie 0,25 punt. Beleidsboek 2.13.5: beschermd
    # stads- of dorpsgezicht +5%.

    dependencies = [
        (
            "puntenteller",
            "0002_alter_gebruikersinvoer_woonvoorziening_handicap_netto_investering",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="kengetal",
            name="bijzondere_voorziening_intercom_met_beeld_factor",
            field=models.DecimalField(decimal_places=2, default=0.25, max_digits=8),
        ),
        migrations.AlterField(
            model_name="kengetal",
            name="monument_beschermd_stads_of_dorpsgezicht_huurprijsopslag_factor",
            field=models.DecimalField(decimal_places=2, default=1.05, max_digits=4),
        ),
    ]
