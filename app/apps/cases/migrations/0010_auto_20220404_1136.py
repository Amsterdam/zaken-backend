# Generated by Django 3.2.7 on 2022-04-04 09:36

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0009_auto_20220307_1344"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="casestate",
            options={"ordering": ["created"]},
        ),
        migrations.RemoveField(
            model_name="casestate",
            name="case_process_id",
        ),
        migrations.RemoveField(
            model_name="casestate",
            name="end_date",
        ),
        migrations.RemoveField(
            model_name="casestate",
            name="information",
        ),
        migrations.RemoveField(
            model_name="casestate",
            name="start_date",
        ),
        migrations.RemoveField(
            model_name="casestate",
            name="users",
        ),
        migrations.RemoveField(
            model_name="casestate",
            name="workflow",
        ),
        migrations.RemoveField(
            model_name="casetheme",
            name="case_state_types_top",
        ),
        migrations.AddField(
            model_name="casestate",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True,
                default=datetime.datetime(2022, 4, 4, 9, 36, 30, 176389, tzinfo=utc),
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="casestate",
            name="status",
            field=models.CharField(
                choices=[
                    ("TOEZICHT", "Toezicht"),
                    ("HANDHAVING", "Handhaving"),
                    ("AFGESLOTEN", "Afgesloten"),
                ],
                default="TOEZICHT",
                max_length=50,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="casestatetype",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="casestatetype",
            name="theme",
        ),
    ]