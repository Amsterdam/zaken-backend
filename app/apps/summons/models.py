from apps.cases.models import Case, CaseTeam
from apps.events.models import CaseEvent, ModelEventEmitter
from apps.summons.const import SUMMON_TYPES
from django.db import models


class SummonType(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, related_name="summons", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class Summon(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_SUMMON

    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.RESTRICT, related_name="summons"
    )
    type = models.ForeignKey(
        to=SummonType, related_name="summons", on_delete=models.RESTRICT
    )
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __get_event_values__(self):
        return {
            "date_added": self.date_added,
            "description": self.description,
            "type": self.type.name,
        }


class SummonedPerson(models.Model):
    first_name = models.CharField(max_length=255)
    preposition = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.preposition} {self.last_name}"
