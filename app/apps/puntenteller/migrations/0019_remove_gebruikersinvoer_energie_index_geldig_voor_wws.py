from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0018_kengetal_zorgwoning_opslag_factor"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="energie_index_geldig_voor_wws",
        ),
    ]
