# Generated by Django 3.1.7 on 2021-04-02 09:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summons", "0008_remove_summon_intention_closing_decision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="summon",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="summons",
                to="cases.case",
            ),
        ),
    ]
