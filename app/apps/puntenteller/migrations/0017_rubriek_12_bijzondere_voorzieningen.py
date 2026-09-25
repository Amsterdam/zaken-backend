from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0016_kengetal_woz_oppervlakte_parkeer_type_1"),
    ]

    operations = [
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="bijzondere_voorziening_laadpalen",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="zorgwoning",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="gebruikersinvoer",
            name="bijzondere_voorziening_intercom_met_beeld",
            field=models.BooleanField(default=False),
        ),
    ]
