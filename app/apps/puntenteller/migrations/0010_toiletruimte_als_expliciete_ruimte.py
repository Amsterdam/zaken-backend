from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0009_verwijder_overbodige_keuken_aanrecht_velden"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="apart_toilet_hangend",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="apart_toilet_staand",
        ),
    ]
