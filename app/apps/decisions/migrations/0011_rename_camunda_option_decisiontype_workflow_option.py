# Generated by Django 3.2.7 on 2021-10-20 11:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("decisions", "0010_rename_camunda_task_id_decision_case_user_task_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="decisiontype",
            old_name="camunda_option",
            new_name="workflow_option",
        ),
    ]