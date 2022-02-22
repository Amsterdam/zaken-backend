from apps.cases.models import Case, CaseTheme
from apps.events.models import CaseEvent, TaskModelEventEmitter
from apps.workflow.models import CaseWorkflow
from django.conf import settings
from django.db import models


class SummonType(models.Model):
    class Meta:
        ordering = ["name"]

    workflow_option = models.CharField(max_length=255, default="aanschrijvingen")
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(
        to=CaseTheme, related_name="summon_types", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.name} - {self.theme}"


class Summon(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_SUMMON

    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.CASCADE, related_name="summons"
    )
    type = models.ForeignKey(
        to=SummonType, related_name="summons", on_delete=models.RESTRICT
    )
    type_result = models.JSONField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT
    )
    # intention_closing_decision = models.BooleanField()

    def __get_person_event_values__(self):
        persons = []

        for person in self.persons.all():
            persons.append(
                {
                    "first_name": person.first_name,
                    "preposition": person.preposition,
                    "last_name": person.last_name,
                    "person_role": person.person_role,
                }
            )

        return persons

    def __get_event_values__(self):
        event_values = {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "description": self.description,
            "type": self.type.name,
            "persons": self.__get_person_event_values__(),
        }
        if isinstance(self.type_result, dict):
            event_values.update(**self.type_result)

        return event_values

    def __str__(self):
        return f"{self.id} Summon - {self.type} - Case {self.case.id}"

    def complete_task(self):
        CaseWorkflow.complete_user_task(
            self.case_user_task_id,
            {
                "type_aanschrijving": {"value": self.type.workflow_option},
                "names": {
                    "value": ", ".join(
                        [person.__str__() for person in self.persons.all()]
                    )
                },
                "summon_id": {"value": self.id},
            },
        )
        return True


class SummonedPerson(models.Model):
    PERSON_ROLE_OWNER = "PERSON_ROLE_OWNER"
    PERSON_ROLE_RESIDENT = "PERSON_ROLE_RESIDENT"
    PERSON_ROLE_MIDDLEMAN = "PERSON_ROLE_MIDDLEMAN"
    PERSON_ROLE_PLATFORM = "PERSON_ROLE_PLATFORM"
    PERSON_ROLE_HEIR = "PERSON_ROLE_HEIR"
    PERSON_ROLE = tuple(
        (role, role)
        for role in [
            PERSON_ROLE_OWNER,
            PERSON_ROLE_RESIDENT,
            PERSON_ROLE_MIDDLEMAN,
            PERSON_ROLE_PLATFORM,
            PERSON_ROLE_HEIR,
        ]
    )
    first_name = models.CharField(max_length=255, null=True, blank=True)
    preposition = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    entity_name = models.CharField(max_length=255, null=True, blank=True)
    function = models.CharField(max_length=255, null=True, blank=True)

    person_role = models.CharField(
        max_length=255,
        choices=PERSON_ROLE,
        default=PERSON_ROLE[0][0],
    )
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
