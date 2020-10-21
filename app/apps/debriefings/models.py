from apps.cases.models import Case
from apps.users.models import User
from django.db import models


class Debriefing(models.Model):
    case = models.ForeignKey(
        to=Case, null=False, on_delete=models.RESTRICT, related_name="debriefings"
    )
    author = models.ForeignKey(
        to=User, null=False, on_delete=models.RESTRICT, related_name="debriefings"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    hit = models.BooleanField(null=False)
    feedback = models.CharField(null=False, blank=False, max_length=255)
