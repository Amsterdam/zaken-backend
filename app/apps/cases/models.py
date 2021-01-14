import uuid

from apps.addresses.models import Address
from apps.camunda.services import CamundaService
from apps.events.models import CaseEvent, ModelEventEmitter
from django.conf import settings
from django.db import models
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver


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


@receiver(post_save, sender=Case, dispatch_uid="case_init_in_camunda")
def create_case_instance_in_camunda(sender, instance, created, **kwargs):
    if created:
        camunda_id = CamundaService().start_instance()
        instance.camunda_id = camunda_id
        instance.save()


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
