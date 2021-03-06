# Generated by Django 3.1.7 on 2021-03-17 17:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0042_auto_20210224_2009"),
    ]

    operations = [
        migrations.CreateModel(
            name="DaySegment",
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
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="cases.caseteam"
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("name", "team")},
            },
        ),
        migrations.CreateModel(
            name="Priority",
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
                ("weight", models.FloatField()),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="cases.caseteam"
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("name", "team")},
            },
        ),
        migrations.CreateModel(
            name="WeekSegment",
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
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="cases.caseteam"
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("name", "team")},
            },
        ),
        migrations.CreateModel(
            name="ScheduleType",
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
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="cases.caseteam"
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "unique_together": {("name", "team")},
            },
        ),
        migrations.CreateModel(
            name="Schedule",
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
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedules",
                        to="cases.case",
                    ),
                ),
                (
                    "day_segment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="schedules.daysegment",
                    ),
                ),
                (
                    "priority",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="schedules.priority",
                    ),
                ),
                (
                    "schedule_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="schedules.scheduletype",
                    ),
                ),
                (
                    "week_segment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="schedules.weeksegment",
                    ),
                ),
            ],
            options={
                "unique_together": {("case", "schedule_type")},
            },
        ),
    ]
