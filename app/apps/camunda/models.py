from apps.cases.models import Case, CaseState
from apps.events.models import CaseEvent, ModelEventEmitter
from django.conf import settings
from django.db import models


class GenericCompletedTask(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_GENERIC_TASK

    case = models.ForeignKey(to=Case, on_delete=models.CASCADE)
    # Note: Once we have working Service Tasks to orchestrate state changes, we'll be able to group events based on state and determine the UI data component using the EVENT_TYPE. This will require some rework in the other ModelEventEmitters.
    state = models.ForeignKey(to=CaseState, on_delete=models.CASCADE, null=True)
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
