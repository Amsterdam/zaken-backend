# Generated by Django 3.1.8 on 2021-05-19 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decisions", "0004_auto_20210318_0953"),
    ]

    operations = [
        migrations.AddField(
            model_name="decision",
            name="camunda_task_id",
            field=models.CharField(default="-1", max_length=50),
        ),
    ]
