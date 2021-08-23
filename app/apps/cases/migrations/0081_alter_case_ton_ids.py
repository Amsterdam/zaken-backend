# Generated by Django 3.2.5 on 2021-08-18 12:24

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0080_case_ton_ids"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="ton_ids",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(),
                blank=True,
                default=list,
                null=True,
                size=None,
            ),
        ),
    ]