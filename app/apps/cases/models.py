import uuid

from apps.addresses.models import Address
from apps.events.models import CaseEvent, ModelEventEmitter
from apps.users.models import User
from django.conf import settings
from django.db import models
from django.utils import timezone


class CaseTeam(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class CaseReason(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, related_name="reasons", on_delete=models.CASCADE
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
    team = models.ForeignKey(to=CaseTeam, on_delete=models.PROTECT)
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT
    )
    reason = models.ForeignKey(to=CaseReason, on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)

    def __get_event_values__(self):
        reason = self.reason.name
        if self.is_legacy_bwv:
            reason = "Deze zaak bestond al voor het nieuwe zaaksysteem. Zie BWV voor de aanleiding(en)."

        if self.author:
            author = self.author.full_name
        else:
            author = "Medewerker onbekend"

        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "reason": reason,
            "description": self.description,
            "author": author,
        }

    def __get_case__(self):
        return self

    def __generate_identification__(self):
        return str(uuid.uuid4())

    def __str__(self):
        if self.identification:
            return f"{self.id} Case - {self.identification}"
        return f"{self.id} Case"

    def get_current_states(self):
        return self.case_states.filter(end_date__isnull=True)

    def set_state(self, state_name):
        state_type, _ = CaseStateType.objects.get_or_create(name=state_name)
        state = CaseState.objects.create(case=self, status=state_type)

        return state

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        if self.identification in (None, ""):
            self.identification = self.__generate_identification__()

        super().save(*args, **kwargs)


class CaseStateType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class CaseState(models.Model):
    class Meta:
        ordering = ["start_date"]

    case = models.ForeignKey(Case, related_name="case_states", on_delete=models.CASCADE)
    status = models.ForeignKey(CaseStateType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="case_states", related_query_name="users"
    )

    def __str__(self):
        return f"{self.start_date} - {self.end_date} - {self.case.identification} - {self.status.name}"

    def end_state(self):
        if not self.end_date:
            self.end_date = timezone.now().date()

        else:
            raise AttributeError("End date is already set")

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        return super().save(*args, **kwargs)
