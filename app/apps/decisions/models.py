from apps.cases.models import Case, CaseTeam
from apps.events.models import CaseEvent, TaskModelEventEmitter
from apps.summons.models import Summon
from django.conf import settings
from django.db import models


class DecisionType(models.Model):
    camunda_option = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_sanction = models.BooleanField(default=False)
    team = models.ForeignKey(
        to=CaseTeam, related_name="decision_types", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.team.name} - {self.name}"

    class Meta:
        ordering = ["name"]


class Decision(TaskModelEventEmitter):
    """
    Model is used to repesent the decision after a summon
    """

    EVENT_TYPE = CaseEvent.TYPE_DECISION

    case = models.ForeignKey(
        to=Case, on_delete=models.CASCADE, related_name="decisions"
    )
    summon = models.OneToOneField(
        to=Summon, on_delete=models.CASCADE, related_name="decision", null=True
    )
    decision_type = models.ForeignKey(to=DecisionType, on_delete=models.RESTRICT)
    sanction_amount = models.DecimalField(
        max_digits=100, decimal_places=2, blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __get_event_values__(self):
        if self.summon:
            persons = self.summon.__get_person_event_values__()
        else:
            persons = []

        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "persons": persons,
            "description": self.description,
            "type": self.decision_type.name,
            "sanction_amount": self.sanction_amount,
        }
