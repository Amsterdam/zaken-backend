# Generated by Django 3.2.7 on 2022-02-14 13:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("cases", "0007_alter_case_ton_ids"),
    ]

    operations = [
        migrations.CreateModel(
            name="Advertisement",
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
                ("link", models.CharField(max_length=255)),
                ("date_added", models.DateTimeField(auto_now_add=True)),
                (
                    "related_object_id",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="advertisements",
                        to="cases.case",
                    ),
                ),
                (
                    "related_object_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
    ]