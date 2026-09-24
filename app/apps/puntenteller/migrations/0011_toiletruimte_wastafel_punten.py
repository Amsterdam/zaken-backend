from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0010_toiletruimte_als_expliciete_ruimte"),
    ]

    operations = [
        migrations.AddField(
            model_name="kengetal",
            name="toiletruimte_meerpersoons_wastafel_max_punten",
            field=models.DecimalField(decimal_places=2, default=1.5, max_digits=8),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="toiletruimte_wastafel_max_punten",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=8),
        ),
    ]
