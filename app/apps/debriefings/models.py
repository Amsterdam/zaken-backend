from apps.cases.models import Case, CaseTimelineSubject, CaseTimelineThread
from apps.users.models import User
from django.db import models


class Debriefing(models.Model):
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

    def save(self, *args, **kwargs):
        # TODO: adding the timeline objects here is done for demo/prototyping purposes. Remove or improve later.
        case_timeline_subject, _ = CaseTimelineSubject.objects.get_or_create(
            case=self.case, subject="Debriefing"
        )
        case_timeline_thread, _ = CaseTimelineThread.objects.get_or_create(
            subject=case_timeline_subject
        )
        # case_timeline_thread.authors = [self.author]
        case_timeline_thread.parameters = {
            "Overtreding": "Ja" if self.violation else "Nee"
        }
        case_timeline_thread.notes = self.feedback
        case_timeline_thread.save()

        return super().save(*args, **kwargs)
