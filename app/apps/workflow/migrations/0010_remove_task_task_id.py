# Generated by Django 3.2.5 on 2021-09-07 08:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0009_auto_20210906_2046"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="task_id",
        ),
    ]