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
            name="Visit",
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
                ("start_time", models.DateTimeField()),
                ("situation", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "observations",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "can_next_visit_go_ahead",
                    models.BooleanField(default=True, null=True),
                ),
                (
                    "can_next_visit_go_ahead_description",
                    models.TextField(blank=True, default=None, null=True),
                ),
                (
                    "suggest_next_visit",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "suggest_next_visit_description",
                    models.TextField(blank=True, default=None, null=True),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("authors", models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="cases.case"
                    ),
                ),
            ],
            options={
                "ordering": ["-start_time"],
            },
        ),
    ]
