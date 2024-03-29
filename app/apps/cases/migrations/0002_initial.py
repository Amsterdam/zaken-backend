# Generated by Django 3.2.7 on 2021-11-16 09:57
import django
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("workflow", "0001_initial"),
        ("addresses", "0001_initial"),
        ("cases", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = []
    operations = [
        migrations.AddField(
            model_name="casestate",
            name="workflow",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="case_states",
                to="workflow.caseworkflow",
            ),
        ),
        migrations.AddField(
            model_name="casereason",
            name="theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reasons",
                to="cases.casetheme",
            ),
        ),
        migrations.AddField(
            model_name="caseproject",
            name="theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.casetheme"
            ),
        ),
        migrations.AddField(
            model_name="caseprocessinstance",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cases.case"
            ),
        ),
        migrations.AddField(
            model_name="casecloseresult",
            name="case_theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.casetheme"
            ),
        ),
        migrations.AddField(
            model_name="caseclosereason",
            name="case_theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.casetheme"
            ),
        ),
        migrations.AddField(
            model_name="caseclose",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="caseclose",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cases.case"
            ),
        ),
        migrations.AddField(
            model_name="caseclose",
            name="reason",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.caseclosereason"
            ),
        ),
        migrations.AddField(
            model_name="caseclose",
            name="result",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="cases.casecloseresult",
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="address",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases",
                to="addresses.address",
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="cases.caseproject",
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="reason",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.casereason"
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.casetheme"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="casestatetype",
            unique_together={("name", "theme")},
        ),
    ]
