import uuid

from apps.cases.models import Case
from django.db import models


class Fine(models.Model):
    identification = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    case = models.ForeignKey(Case, related_name="fines", on_delete=models.CASCADE)

    def __str__(self):
        if self.identification:
            return self.identification
        return ""

    def save(self, *args, **kwargs):
        if not self.identification:
            self.identification = str(uuid.uuid4())

        super().save(*args, **kwargs)
