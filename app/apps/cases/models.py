import uuid

from apps.addresses.models import Address
from apps.users.models import User
from django.db import models


class Case(models.Model):
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


# TODO: Consider moving this to a dedicated timelines/events app
class CaseTimelineSubject(models.Model):
    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="case_timeline_subjects"
    )
    subject = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)


class CaseTimelineThread(models.Model):
    # TODO Not sure if all authors are Users
    authors = models.ManyToManyField(to=User, related_name="authors")
    date = models.DateField(auto_now_add=True)
    subject = models.ForeignKey(CaseTimelineSubject, on_delete=models.CASCADE)
    parameters = models.JSONField(default={})
    notes = models.TextField(blank=True, null=True)


class CaseTimelineReaction(models.Model):
    timeline_item = models.ForeignKey(CaseTimelineThread, on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)
    comment = models.TextField()
    date = models.DateField(auto_now_add=True)
