from apps.decisions.models import Decision
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Decision, dispatch_uid="decision")
def update_decision_with_summon(sender, instance, created, **kwargs):
    """
    TODO: Temporary hook to update decision with a summon instance.
    This will be resolved when we support multiple summons.

    TODO: This isn't called because this signals file isn't registered in the apps.py
    """
    if created:
        # TODO: create belastingdienst number
        if instance.case.summons.count() == 1:
            instance.summon = instance.case.summons.all()[0]
            instance.save()
