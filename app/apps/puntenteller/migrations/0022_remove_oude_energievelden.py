from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0021_extra_monumenttypen"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="energieprestatie_individuele_woonruimte",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="energieprestatie_peildatum",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="energieprestatie_registratiedatum",
        ),
    ]
