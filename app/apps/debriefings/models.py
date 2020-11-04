from apps.cases.models import Case
from apps.events.models import CaseEvent, ModelEventEmitter
from apps.users.models import User
from django.db import models
from utils.class_mixins import ModelEditableTimeConstraint


class Debriefing(ModelEventEmitter, ModelEditableTimeConstraint):
    EVENT_TYPE = CaseEvent.TYPE_DEBRIEFING
    # TODO: Determine the time this is editable. Making it 24 for now
    EDITABLE_TIME_IN_SECONDS = 60 * 60 * 24

    VIOLATION_NO = "NO"
    VIOLATION_YES = "YES"
    VIOLATION_ADDITIONAL_RESEARCH_REQUIRED = "ADDITIONAL_RESEARCH_REQUIRED"

    VIOLATION_CHOICES = [
        (VIOLATION_NO, "No"),
        (VIOLATION_YES, "Yes"),
        (VIOLATION_ADDITIONAL_RESEARCH_REQUIRED, "Additional research required"),
    ]

    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.RESTRICT, related_name="debriefings"
    )
    author = models.ForeignKey(
        to=User, null=False, on_delete=models.RESTRICT, related_name="debriefings"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    violation = models.CharField(
        max_length=28,
        choices=VIOLATION_CHOICES,
        default=VIOLATION_NO,
    )
    feedback = models.CharField(null=False, blank=False, max_length=255)

    def __get_event_values__(self):
        return {
            "author": self.author.full_name,
            "date_added": self.date_added,
            "violation": self.violation,
            "feedback": self.feedback,
        }
