import uuid

from apps.addresses.models import Address
from apps.events.models import Event, ModelEventEmitter
from apps.users.models import User
from django.db import models


class Case(ModelEventEmitter):
    EVENT_TYPE = Event.TYPE_CASE

    class Meta:
        ordering = ["start_date"]

    identification = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    address = models.ForeignKey(
        to=Address, null=True, on_delete=models.CASCADE, related_name="cases"
    )

    def __get_event_values__(self):
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            # TODO: This is hardcoded and will be dynamic at a later point
            "reason": "Deze zaak bestond al voor het nieuwe zaaksysteem. Zie BWV voor de aanleiding(en).",
        }

    def __get_case__(self):
        return self

    def get_current_state(self):
        if self.case_states.count() > 0:
            return self.case_states.all().order_by("-state_date").first()
        return None

    def __str__(self):
        if self.identification:
            return f"Case {self.id} - {self.identification}"
        return f"Case {self.id}"

    def save(self, *args, **kwargs):
        if not self.identification:
            self.identification = str(uuid.uuid4())

        super().save(*args, **kwargs)


class CaseStateType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CaseState(models.Model):
    case = models.ForeignKey(Case, related_name="case_states", on_delete=models.CASCADE)
    status = models.ForeignKey(CaseStateType, on_delete=models.PROTECT)
    state_date = models.DateField()
    users = models.ManyToManyField(
        User, related_name="case_states", related_query_name="users"
    )

    def __str__(self):
        return f"{self.state_date} - {self.case.identification} - {self.status.name}"
