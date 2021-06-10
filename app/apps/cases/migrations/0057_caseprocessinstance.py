# Generated by Django 3.1.8 on 2021-05-26 12:29

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0056_casestate_information"),
    ]

    operations = [
        migrations.CreateModel(
            name="CaseProcessInstance",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "process_id",
                    models.CharField(default=uuid.uuid4, max_length=255, unique=True),
                ),
                (
                    "camunda_process_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="cases.case"
                    ),
                ),
            ],
        ),
    ]