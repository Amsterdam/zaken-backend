from apps.cases.models import Case
from apps.events.models import CaseEvent, TaskModelEventEmitter
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Visit(TaskModelEventEmitter):
    SITUATION_NOBODY_PRESENT = "nobody_present"
    SITUATION_NO_COOPERATION = "no_cooperation"
    SITUATION_ACCESS_GRANTED = "access_granted"

    SITUATIONS = (
        (SITUATION_NOBODY_PRESENT, "Niemand aanwezig"),
        (SITUATION_NO_COOPERATION, "Geen medewerking"),
        (SITUATION_ACCESS_GRANTED, "Toegang verleend"),
    )

    EVENT_TYPE = CaseEvent.TYPE_VISIT

    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    situation = models.CharField(max_length=255, null=True, blank=True)
    observations = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    can_next_visit_go_ahead = models.BooleanField(default=True, null=True)
    can_next_visit_go_ahead_description = models.TextField(
        null=True, blank=True, default=None
    )
    suggest_next_visit = models.CharField(max_length=50, null=True, blank=True)
    suggest_next_visit_description = models.TextField(
        null=True, blank=True, default=None
    )
    authors = models.ManyToManyField(settings.AUTH_USER_MODEL)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"Case: {self.case.id} - {self.id}"

    def __get_event_values__(self):
        json_obj = {
            "start_time": self.start_time,
            "authors": [],
            "situation": self.situation,
            "observations": self.observations,
            "can_next_visit_go_ahead": self.can_next_visit_go_ahead,
            "can_next_visit_go_ahead_description": self.can_next_visit_go_ahead_description,
            "suggest_next_visit": self.suggest_next_visit,
            "suggest_next_visit_description": self.suggest_next_visit_description,
        }
        if self.notes:
            json_obj["notes"] = self.notes
        if self.authors:
            json_obj["authors"] = [author.full_name for author in self.authors.all()]

        return json_obj
