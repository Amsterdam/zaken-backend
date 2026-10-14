from django.db import migrations, models


class Migration(migrations.Migration):
    # Beleidsboek 2.11.1: minimum WOZ-waarde als er geen WOZ-waarde bekend is.

    dependencies = [
        ("puntenteller", "0003_kengetal_intercom_en_beschermd_gezicht"),
    ]

    operations = [
        migrations.AddField(
            model_name="kengetal",
            name="woz_minimum_waarde_per_ingangsdatum",
            field=models.JSONField(default=dict),
        ),
    ]
