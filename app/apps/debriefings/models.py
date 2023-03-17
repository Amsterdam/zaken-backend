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
    VIOLATION_LIKELY_INHABITED = "LIKELY_INHABITED"

    VIOLATION_CHOICES = [
        (VIOLATION_NO, "Geen overtreding"),
        (VIOLATION_YES, "Overtreding"),
        (VIOLATION_ADDITIONAL_RESEARCH_REQUIRED, "Nader intern onderzoek nodig"),
        (VIOLATION_ADDITIONAL_VISIT_REQUIRED, "Aanvullend bezoek nodig"),
        (
            VIOLATION_ADDITIONAL_VISIT_WITH_AUTHORIZATION,
            "Machtiging benodigd",
        ),
        (VIOLATION_SEND_TO_OTHER_THEME, "Naar ander thema"),
        (VIOLATION_LIKELY_INHABITED, "Vermoeden bewoning/leegstand"),
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
    violation_result = models.JSONField(null=True, blank=True)
    feedback = models.TextField(null=False, blank=False)
    nuisance_detected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.case.id} Case - Debriefing {self.id}"

    def __get_event_values__(self):
        event_values = {
            "author": self.author.full_name,
            "date_added": self.date_added,
            "violation": self.violation,
            "feedback": self.feedback,
            "nuisance_detected": self.nuisance_detected,
        }
        if isinstance(self.violation_result, dict):
            event_values.update(**self.violation_result)

        return event_values

    def get_violation_choices_by_theme(theme_id):
        # VIOLATION_LIKELY_INHABITED is unavailable for other themes than Leegstand.
        if theme_id == 5:
            return Debriefing.VIOLATION_CHOICES
        else:
            return [
                vc
                for vc in Debriefing.VIOLATION_CHOICES
                if vc[0] != Debriefing.VIOLATION_LIKELY_INHABITED
            ]
