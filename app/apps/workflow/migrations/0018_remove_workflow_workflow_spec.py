# Generated by Django 3.2.5 on 2021-09-21 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0017_auto_20210921_0946"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="workflow",
            name="workflow_spec",
        ),
    ]