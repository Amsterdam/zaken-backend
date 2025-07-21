from apps.cases.models import Case
from apps.events.models import CaseEvent, TaskModelEventEmitter
from django.conf import settings
from django.db import models


class ViolationType(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    theme = models.ForeignKey(
        to="cases.CaseTheme",
        null=True,
        on_delete=models.CASCADE,
        related_name="violation_types",
    )

    def __str__(self):
        return f"{self.name} - {self.theme}"


class Debriefing(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_DEBRIEFING

    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.CASCADE, related_name="debriefings"
    )
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=False,
        on_delete=models.RESTRICT,
        related_name="debriefings",
    )
    # TODO: Maybe rename this to date_created for consistency?
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    violation = models.ForeignKey(
        to="ViolationType",
        null=True,
        on_delete=models.SET_NULL,
        related_name="debriefings",
    )
    violation_old = models.CharField(
        max_length=255,
        default="NO",
    )
    violation_result = models.JSONField(null=True, blank=True)
    feedback = models.TextField(null=False, blank=False)
    nuisance_detected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.case.id} Case - Debriefing {self.id}"

    def __get_event_values__(self):
        event_values = {
            "author": self.author.full_name,
            "date_added": self.date_added,
            "violation": self.violation.value,
            "feedback": self.feedback,
            "nuisance_detected": self.nuisance_detected,
        }
        if isinstance(self.violation_result, dict):
            event_values.update(**self.violation_result)

        return event_values

    def get_violation_choices_by_theme(theme_id):
        return ViolationType.objects.filter(
            theme_id=theme_id,
            enabled=True,
        ).values_list("id", "value", "name")
