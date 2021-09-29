# Generated by Django 3.2.7 on 2021-09-25 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0019_task_updated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workflow",
            name="workflow_type",
            field=models.CharField(
                choices=[
                    ("main_workflow", "main_workflow"),
                    ("sub_workflow", "sub_workflow"),
                    ("visit", "visit"),
                ],
                default="main_workflow",
                max_length=100,
            ),
        ),
    ]