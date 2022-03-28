from apps.schedules.models import Schedule
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Schedule, dispatch_uid="pre_save_schedule")
def pre_save_schedule(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    if not instance.id:
        is_corpo_combiteam_completed_tasks = bool(
            instance.case.generic_completed_tasks.filter(
                task_name__in=(
                    "task_contacteren_corporatie_voor_huisbezoek",
                    "task_monitoren_reactie_corporatie_voor_huisbezoek",
                ),
                variables__reactie_ontvangen_voor_huisbezoek__value="samen_lopen",
            )
        )
        is_combiteam_project = bool(
            instance.case.project
            and instance.case.project.name
            in [
                "Combi BI Doorpak",
                "Combi BI Melding",
                "Combi Doorpak",
                "Combi Melding",
                "Combi Overbewoning",
                "Combi_ZKL_Doorpak",
                "Combi_ZKL_Melding",
                "ZKL Combi OenA",
            ]
        )
        instance.housing_corporation_combiteam = (
            is_corpo_combiteam_completed_tasks | is_combiteam_project
        )


@receiver(post_save, sender=Schedule, dispatch_uid="schedule_create_complete_task")
def complete_task_create_schedule(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})
