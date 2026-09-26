from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0015_parkeerruimten_als_objecten"),
    ]

    operations = [
        migrations.AddField(
            model_name="kengetal",
            name="woz_oppervlakte_parkeer_type_1",
            field=models.DecimalField(decimal_places=2, default=12.0, max_digits=8),
        ),
    ]
