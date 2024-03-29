# Generated by Django 3.2.7 on 2021-11-16 09:57
import django
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = []
    operations = [
        migrations.CreateModel(
            name="Debriefing",
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
                ("case_user_task_id", models.CharField(default="-1", max_length=255)),
                ("date_added", models.DateTimeField(auto_now_add=True)),
                ("date_modified", models.DateTimeField(auto_now=True)),
                (
                    "violation",
                    models.CharField(
                        choices=[
                            ("NO", "No"),
                            ("YES", "Yes"),
                            (
                                "ADDITIONAL_RESEARCH_REQUIRED",
                                "Additional research required",
                            ),
                            ("ADDITIONAL_VISIT_REQUIRED", "Nieuw huisbezoek nodig"),
                            (
                                "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
                                "Nieuw huisbezoek inclusief machtingaanvraag",
                            ),
                            ("SEND_TO_OTHER_THEME", "Naar ander team"),
                        ],
                        default="NO",
                        max_length=255,
                    ),
                ),
                ("violation_result", models.JSONField(blank=True, null=True)),
                ("feedback", models.TextField()),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="debriefings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debriefings",
                        to="cases.case",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
