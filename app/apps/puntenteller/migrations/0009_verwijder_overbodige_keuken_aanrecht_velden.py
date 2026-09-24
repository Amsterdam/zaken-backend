from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0008_corrigeer_keuken_aanrecht_staffel"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="kengetal",
            name="keuken_aanrecht_grens_4",
        ),
        migrations.RemoveField(
            model_name="kengetal",
            name="keuken_aanrecht_punten_4",
        ),
        migrations.RemoveField(
            model_name="kengetal",
            name="keuken_aanrecht_punten_5",
        ),
    ]
