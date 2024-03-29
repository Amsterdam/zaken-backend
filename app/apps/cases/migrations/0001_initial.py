# Generated by Django 3.2.7 on 2021-11-16 09:57

import uuid

import django
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = []
    operations = [
        migrations.CreateModel(
            name="Case",
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
                    "identification",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                ("start_date", models.DateField(null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("is_legacy_bwv", models.BooleanField(default=False)),
                ("is_legacy_camunda", models.BooleanField(default=False)),
                (
                    "legacy_bwv_case_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                (
                    "directing_process",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "camunda_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255),
                        blank=True,
                        default=list,
                        null=True,
                        size=None,
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "ton_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        null=True,
                        size=None,
                    ),
                ),
            ],
            options={
                "ordering": ["-start_date"],
            },
        ),
        migrations.CreateModel(
            name="CaseClose",
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
                ("description", models.TextField()),
                ("date_added", models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CaseCloseReason",
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
                ("result", models.BooleanField()),
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ["case_theme", "name"],
            },
        ),
        migrations.CreateModel(
            name="CaseCloseResult",
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
                ("name", models.CharField(max_length=255)),
            ],
        ),
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
            ],
        ),
        migrations.CreateModel(
            name="CaseProject",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ["theme", "name"],
            },
        ),
        migrations.CreateModel(
            name="CaseReason",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="CaseStateType",
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
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="CitizenReport",
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
                (
                    "reporter_name",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "reporter_phone",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "reporter_email",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("identification", models.PositiveIntegerField()),
                (
                    "advertisement_linklist",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255),
                        blank=True,
                        default=list,
                        null=True,
                        size=None,
                    ),
                ),
                ("description_citizenreport", models.TextField(blank=True, null=True)),
                ("nuisance", models.BooleanField(default=False)),
                ("date_added", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="case_citizen_reports",
                        to="cases.case",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CaseTheme",
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
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "case_state_types_top",
                    models.ManyToManyField(blank=True, to="cases.CaseStateType"),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="casestatetype",
            name="theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="state_types",
                to="cases.casetheme",
            ),
        ),
        migrations.CreateModel(
            name="CaseState",
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
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                (
                    "information",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "case_process_id",
                    models.CharField(default="", max_length=255, null=True),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="case_states",
                        to="cases.case",
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="cases.casestatetype",
                    ),
                ),
                (
                    "users",
                    models.ManyToManyField(
                        related_name="case_states",
                        related_query_name="users",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["start_date"],
            },
        ),
    ]
