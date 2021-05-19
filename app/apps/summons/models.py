from apps.cases.models import Case, CaseTeam
from apps.events.models import CaseEvent, ModelEventEmitter
from django.conf import settings
from django.db import models


class SummonType(models.Model):
    class Meta:
        ordering = ["name"]

    camunda_option = models.CharField(max_length=255, default="aanschrijvingen")
    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, related_name="summon_types", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class Summon(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_SUMMON
    camunda_task_id = models.CharField(max_length=50, default="-1")

    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.CASCADE, related_name="summons"
    )
    type = models.ForeignKey(
        to=SummonType, related_name="summons", on_delete=models.RESTRICT
    )
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT
    )
    # intention_closing_decision = models.BooleanField()

    def __get_person_event_values__(self):
        persons = []

        for person in self.persons.all():
            persons.append(person.__str__())

        return persons

    def __get_event_values__(self):
        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "description": self.description,
            "type": self.type.name,
            "persons": self.__get_person_event_values__(),
        }

    def __str__(self):
        return f"{self.id} Summon - {self.type} - Case {self.case.id}"


class SummonedPerson(models.Model):
    first_name = models.CharField(max_length=255)
    preposition = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255)
    summon = models.ForeignKey(
        to=Summon,
        related_name="persons",
        on_delete=models.CASCADE,
        blank=False,
        null=True,
    )

    def __str__(self):
        if self.preposition:
            return f"{self.first_name} {self.preposition} {self.last_name}"

        return f"{self.first_name} {self.last_name}"
