from django.db import migrations, models


def corrigeer_keuken_aanrecht_staffel(apps, schema_editor):
    Kengetal = apps.get_model("puntenteller", "Kengetal")
    Kengetal.objects.update(
        keuken_aanrecht_grens_3=2,
        keuken_aanrecht_grens_4=2,
        keuken_aanrecht_punten_4=7,
        keuken_aanrecht_punten_5=7,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0007_gebruikersinvoer_bouwjaar_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="kengetal",
            name="keuken_aanrecht_grens_3",
            field=models.DecimalField(decimal_places=2, default=2.0, max_digits=8),
        ),
        migrations.AlterField(
            model_name="kengetal",
            name="keuken_aanrecht_grens_4",
            field=models.DecimalField(decimal_places=2, default=2.0, max_digits=8),
        ),
        migrations.AlterField(
            model_name="kengetal",
            name="keuken_aanrecht_punten_4",
            field=models.DecimalField(decimal_places=2, default=7.0, max_digits=8),
        ),
        migrations.AlterField(
            model_name="kengetal",
            name="keuken_aanrecht_punten_5",
            field=models.DecimalField(decimal_places=2, default=7.0, max_digits=8),
        ),
        migrations.RunPython(
            corrigeer_keuken_aanrecht_staffel,
            migrations.RunPython.noop,
        ),
    ]
