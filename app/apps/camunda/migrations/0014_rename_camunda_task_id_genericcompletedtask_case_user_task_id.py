# Generated by Django 3.2.7 on 2021-10-13 12:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("camunda", "0013_alter_camundaprocess_theme"),
    ]

    operations = [
        migrations.RenameField(
            model_name="genericcompletedtask",
            old_name="camunda_task_id",
            new_name="case_user_task_id",
        ),
    ]