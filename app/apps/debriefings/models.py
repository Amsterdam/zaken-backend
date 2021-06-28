from apps.cases.models import Case
from apps.events.models import CaseEvent, TaskModelEventEmitter
from django.conf import settings
from django.db import models


class Debriefing(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_DEBRIEFING

    VIOLATION_NO = "NO"
    VIOLATION_YES = "YES"
    VIOLATION_ADDITIONAL_RESEARCH_REQUIRED = "ADDITIONAL_RESEARCH_REQUIRED"
    VIOLATION_ADDITIONAL_VISIT_REQUIRED = "ADDITIONAL_VISIT_REQUIRED"
    VIOLATION_ADDITIONAL_VISIT_WITH_AUTHORIZATION = (
        "ADDITIONAL_VISIT_WITH_AUTHORIZATION"
    )
    VIOLATION_SEND_TO_OTHER_THEME = "SEND_TO_OTHER_THEME"

    VIOLATION_CHOICES = [
        (VIOLATION_NO, "No"),
        (VIOLATION_YES, "Yes"),
        (VIOLATION_ADDITIONAL_RESEARCH_REQUIRED, "Additional research required"),
        (VIOLATION_ADDITIONAL_VISIT_REQUIRED, "Nieuw huisbezoek nodig"),
        (
            VIOLATION_ADDITIONAL_VISIT_WITH_AUTHORIZATION,
            "Nieuw huisbezoek inclusief machtingaanvraag",
        ),
        (VIOLATION_SEND_TO_OTHER_THEME, "Naar ander team"),
    ]

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
    violation = models.CharField(
        max_length=255,
        choices=VIOLATION_CHOICES,
        default=VIOLATION_NO,
    )
    violation_result = models.JSONField(null=True)
    feedback = models.CharField(null=False, blank=False, max_length=255)

    def __str__(self):
        return f"{self.case.id} Case - Debriefing {self.id}"

    def __get_event_values__(self):
        event_values = {
            "author": self.author.full_name,
            "date_added": self.date_added,
            "violation": self.violation,
            "feedback": self.feedback,
        }
        if isinstance(self.violation_result, dict):
            event_values.update(**self.violation_result)

        return event_values
