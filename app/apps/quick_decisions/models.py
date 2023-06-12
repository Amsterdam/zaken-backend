from apps.cases.models import Case, CaseTheme
from apps.events.models import CaseEvent, TaskModelEventEmitter
from apps.summons.models import Summon
from django.conf import settings
from django.db import models


class QuickDecisionType(models.Model):
    name = models.CharField(max_length=255)
    workflow_option = models.CharField(max_length=255)
    theme = models.ForeignKey(
        to=CaseTheme, related_name="quick_decision_types", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.theme.name} - {self.name}"

    class Meta:
        ordering = ["name"]


class QuickDecision(TaskModelEventEmitter):
    """
    Model is used to repesent a quick decision
    """

    EVENT_TYPE = CaseEvent.TYPE_DECISION

    case = models.ForeignKey(
        to=Case, on_delete=models.CASCADE, related_name="quick_decisions"
    )
    summon = models.OneToOneField(
        to=Summon, on_delete=models.CASCADE, related_name="quick_decision", null=True
    )
    quick_decision_type = models.ForeignKey(
        to=QuickDecisionType, on_delete=models.RESTRICT
    )
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __get_event_values__(self):
        persons = []
        if self.summon:
            persons = self.summon.__get_person_event_values__()

        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "persons": persons,
            "description": self.description,
            "type": self.quick_decision_type.name,
        }

    def __str__(self):
        if not self.summon:
            return f"{self.id} Quick decision - {self.quick_decision_type.name} - Case {self.case.id} - {self.date_added.strftime('%d-%m-%Y')}"
        names = ", ".join([person.__str__() for person in self.summon.persons.all()])
        return f"{self.id} Quick decision - {self.quick_decision_type.name} - Case {self.case.id} - {names} - {self.date_added.strftime('%d-%m-%Y')}"
