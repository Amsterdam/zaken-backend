from django.db import migrations, models


class Migration(migrations.Migration):
    # Beleidsboek bijlage 3: maximale huurprijs per punt.

    dependencies = [
        ("puntenteller", "0004_kengetal_woz_minimum_waarde"),
    ]

    operations = [
        migrations.AddField(
            model_name="kengetal",
            name="huurprijstabel_per_ingangsdatum",
            field=models.JSONField(default=dict),
        ),
    ]
