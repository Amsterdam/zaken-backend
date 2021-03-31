from apps.cases.models import Case, CaseTeam
from apps.events.models import CaseEvent, ModelEventEmitter
from django.db import models


class Action(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, on_delete=models.CASCADE, related_name="actions"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "team"]


class WeekSegment(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, on_delete=models.CASCADE, related_name="week_segments"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "team"]


class DaySegment(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, on_delete=models.CASCADE, related_name="day_segments"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "team"]


class Priority(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(
        to=CaseTeam, on_delete=models.CASCADE, related_name="priorities"
    )
    weight = models.FloatField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["weight"]
        unique_together = ["name", "team"]


class Schedule(ModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_SCHEDULE

    action = models.ForeignKey(to=Action, on_delete=models.CASCADE)
    week_segment = models.ForeignKey(to=WeekSegment, on_delete=models.CASCADE)
    day_segment = models.ForeignKey(to=DaySegment, on_delete=models.CASCADE)
    priority = models.ForeignKey(to=Priority, on_delete=models.CASCADE)
    case = models.ForeignKey(
        to=Case, related_name="schedules", on_delete=models.CASCADE
    )
