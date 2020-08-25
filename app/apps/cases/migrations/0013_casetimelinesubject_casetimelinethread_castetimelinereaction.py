# Generated by Django 3.1 on 2020-08-24 04:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cases", "0012_statetype_invoice_available"),
    ]

    operations = [
        migrations.CreateModel(
            name="CaseTimelineSubject",
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
                ("subject", models.CharField(max_length=255)),
                ("is_done", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="CaseTimelineThread",
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
                ("date", models.DateField(auto_now_add=True)),
                ("parameters", models.JSONField(default={})),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "authors",
                    models.ManyToManyField(
                        related_name="authors", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cases.casetimelinesubject",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CaseTimelineReaction",
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
                ("comment", models.TextField()),
                ("date", models.DateField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "timeline_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cases.casetimelinethread",
                    ),
                ),
            ],
        ),
    ]
