# Generated by Django 3.2.7 on 2022-03-07 12:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0008_advertisement"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="case",
            name="camunda_ids",
        ),
        migrations.AddField(
            model_name="case",
            name="mma_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="previous_case",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cases.case",
            ),
        ),
    ]
