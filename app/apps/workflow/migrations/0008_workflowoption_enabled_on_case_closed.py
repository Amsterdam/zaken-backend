# Generated by Django 3.2.13 on 2022-05-25 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0007_genericcompletedtask_task_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="workflowoption",
            name="enabled_on_case_closed",
            field=models.BooleanField(default=False),
        ),
    ]