from apps.cases.models import Case
from apps.events.models import CaseEvent, ModelEventEmitter
from django.conf import settings
from django.db import models


class GenericCompletedTask(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_GENERIC_TASK

    case = models.ForeignKey(to=Case, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    variables = models.JSONField(null=True)

    def __get_event_values__(self):

        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "description": self.description,
            "variables": self.variables,
        }


class CamundaProcess(models.Model):
    name = models.CharField(max_length=255)
    camunda_message_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.camunda_message_name}"

    class Meta:
        ordering = ["name"]
