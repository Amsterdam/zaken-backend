# Generated by Django 3.1.7 on 2021-04-02 09:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("debriefings", "0007_auto_20201125_2146"),
    ]

    operations = [
        migrations.AlterField(
            model_name="debriefing",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="debriefings",
                to="cases.case",
            ),
        ),
    ]
