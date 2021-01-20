import uuid

from apps.addresses.models import Address
from apps.events.models import CaseEvent, ModelEventEmitter
from django.conf import settings
from django.db import models


class CaseTeam(models.Model):
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name


class CaseReason(models.Model):
    name = models.CharField(max_length=255, null=False)
    case_team = models.ForeignKey(
        to=CaseTeam, null=False, related_name="case_reasons", on_delete=models.PROTECT
    )

    def __str__(self):
        return self.name


class Case(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_CASE

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
    is_legacy_bwv = models.BooleanField(default=False)
    camunda_id = models.CharField(max_length=255, null=True, blank=True)
    case_team = models.ForeignKey(to=CaseTeam, null=True, on_delete=models.PROTECT)
    case_reason = models.ForeignKey(to=CaseReason, null=True, on_delete=models.PROTECT)

    def __get_event_values__(self):
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "reason": self.case_reason,
        }

    def __get_case__(self):
        return self

    def __generate_identification__(self):
        return str(uuid.uuid4())

    def __str__(self):
        if self.identification:
            return f"Case {self.id} - {self.identification}"
        return f"Case {self.id}"

    def get_current_state(self):
        if self.case_states.count() > 0:
            return self.case_states.all().order_by("-state_date").first()

    def save(self, *args, **kwargs):
        if not self.identification:
            self.identification = self.__generate_identification__()

        super().save(*args, **kwargs)


class CaseStateType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class CaseState(models.Model):
    case = models.ForeignKey(Case, related_name="case_states", on_delete=models.CASCADE)
    status = models.ForeignKey(CaseStateType, on_delete=models.PROTECT)
    state_date = models.DateField()
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="case_states", related_query_name="users"
    )

    def __str__(self):
        return f"{self.state_date} - {self.case.identification} - {self.status.name}"
