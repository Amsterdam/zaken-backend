# Generated by Django 3.1.8 on 2021-05-20 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schedules", "0008_schedule_camunda_task_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedule",
            name="camunda_task_id",
            field=models.CharField(default="-1", max_length=255),
        ),
    ]
