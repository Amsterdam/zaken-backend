from apps.cases.models import Case
from apps.events.models import CaseEvent, ModelEventEmitter
from django.conf import settings
from django.db import models


class Debriefing(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_DEBRIEFING

    VIOLATION_NO = "NO"
    VIOLATION_YES = "YES"
    VIOLATION_ADDITIONAL_RESEARCH_REQUIRED = "ADDITIONAL_RESEARCH_REQUIRED"
    VIOLATION_ADDITIONAL_VISIT_REQUIRED = "ADDITIONAL_VISIT_REQUIRED"

    VIOLATION_CHOICES = [
        (VIOLATION_NO, "No"),
        (VIOLATION_YES, "Yes"),
        (VIOLATION_ADDITIONAL_RESEARCH_REQUIRED, "Additional research required"),
        (VIOLATION_ADDITIONAL_VISIT_REQUIRED, "Nieuw huisbezoek nodig"),
    ]

    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.RESTRICT, related_name="debriefings"
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
    violation = models.CharField(
        max_length=28,
        choices=VIOLATION_CHOICES,
        default=VIOLATION_NO,
    )
    feedback = models.CharField(null=False, blank=False, max_length=255)

    def __str__(self):
        return f"{self.case.id} Case - Debriefing {self.id}"

    def __get_event_values__(self):
        return {
            "author": self.author.full_name,
            "date_added": self.date_added,
            "violation": self.violation,
            "feedback": self.feedback,
        }
