# Generated by Django 3.1.7 on 2021-04-06 13:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("camunda", "0004_remove_genericcompletedtask_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="genericcompletedtask",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cases.case"
            ),
        ),
    ]
