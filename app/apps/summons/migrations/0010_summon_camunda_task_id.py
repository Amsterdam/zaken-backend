# Generated by Django 3.1.8 on 2021-05-19 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summons", "0009_auto_20210402_1103"),
    ]

    operations = [
        migrations.AddField(
            model_name="summon",
            name="camunda_task_id",
            field=models.CharField(default="-1", max_length=50),
        ),
    ]
