from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0017_rubriek_12_bijzondere_voorzieningen"),
    ]

    operations = [
        migrations.AddField(
            model_name="kengetal",
            name="zorgwoning_opslag_factor",
            field=models.DecimalField(decimal_places=2, default=1.35, max_digits=4),
        ),
    ]
