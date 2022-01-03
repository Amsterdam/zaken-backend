# Generated by Django 3.2.7 on 2021-12-22 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0003_auto_20211221_1656"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caseworkflow",
            name="workflow_type",
            field=models.CharField(
                choices=[
                    ("main_workflow", "main_workflow"),
                    ("sub_workflow", "sub_workflow"),
                    ("debrief", "debrief"),
                    ("closing_procedure", "closing_procedure"),
                    ("director", "director"),
                    ("visit", "visit"),
                    ("summon", "summon"),
                    ("decision", "decision"),
                    ("renounce_decision", "renounce_decision"),
                    ("close_case", "close_case"),
                    ("digital_surveillance", "digital_surveillance"),
                    ("housing_corporation", "housing_corporation"),
                ],
                default="director",
                max_length=100,
            ),
        ),
    ]