from apps.cases.models import Case, CaseState
from apps.events.models import ModelEventEmitter
from django.conf import settings
from django.db import models


class GenericCompletedTask(ModelEventEmitter):
    case = models.ForeignKey(to=Case, on_delete=models.RESTRICT)
    state = models.ForeignKey(to=CaseState, on_delete=models.RESTRICT)
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __get_event_type__(self):
        return self.state.status

    def __get_event_values__(self):

        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "description": self.description,
        }
