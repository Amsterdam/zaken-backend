import apps.puntenteller.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0014_buitenruimten_als_objecten"),
    ]

    operations = [
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="parkeerruimten",
            field=models.JSONField(
                blank=True,
                default=apps.puntenteller.models.default_extra_ruimten,
            ),
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="bijzondere_voorziening_laadpaal",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="parkeerruimte_buiten_bij_complex_met_dak",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="parkeerruimte_buiten_bij_complex_zonder_dak",
        ),
        migrations.RemoveField(
            model_name="gebruikersinvoer",
            name="parkeerruimte_gesloten_garage_bij_complex",
        ),
    ]
