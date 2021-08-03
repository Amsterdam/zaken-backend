from apps.cases.models import Case, CaseTheme
from apps.events.models import CaseEvent, TaskModelEventEmitter
from django.conf import settings
from django.db import models


class GenericCompletedTask(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_GENERIC_TASK

    case = models.ForeignKey(to=Case, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    variables = models.JSONField(null=True)

    def __get_event_values__(self):

        # replace in variables value for key 'value', with the value of entry with key 'value_verbose'
        # remove variables with key 'value_verbose'
        variables = dict(
            (k, {**v, **{"value": v.get("value_verbose")}})
            for k, v in self.variables.items()
        )
        variables = dict(
            (k, dict((kk, vv) for kk, vv in v.items() if kk != "value_verbose"))
            for k, v in variables.items()
        )

        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "description": self.description,
            "variables": variables,
        }


class CamundaProcess(models.Model):
    name = models.CharField(max_length=255)
    camunda_message_name = models.CharField(max_length=255)
    to_directing_proccess = models.BooleanField(default=False)
    theme = models.ForeignKey(CaseTheme, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.camunda_message_name}"

    class Meta:
        ordering = ["name"]
