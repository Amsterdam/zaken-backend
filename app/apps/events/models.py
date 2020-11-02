from apps.cases.models import Case
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Event(models.Model):
    TYPE_DEBRIEFING = "DEBRIEFING"
    TYPE_VISIT = "VISIT"
    TYPES = (
        (TYPE_DEBRIEFING, TYPE_DEBRIEFING),
        (TYPE_VISIT, TYPE_VISIT),
    )

    date_created = models.DateTimeField(auto_now_add=True)
    case = models.ForeignKey(
        to=Case,
        on_delete=models.CASCADE,
        related_name="events",
    )
    type = models.CharField(max_length=250, null=False, blank=False, choices=TYPES)
    emitter_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    emitter_id = models.PositiveIntegerField()
    emitter = GenericForeignKey("emitter_type", "emitter_id")

    @property
    def event_values(self):
        """
        Returns a dictionary with EventValues
        """
        event_values = self.emitter.__get_event_values__()
        return event_values


class ModelEventEmitter(models.Model):
    EVENT_TYPE = None

    class Meta:
        abstract = True

    case = None

    def __get_case__(self):
        if self.case:
            return self.case

        raise NotImplementedError("No case relation set")

    def __get_event_type__(self):
        if self.EVENT_TYPE:
            return self.EVENT_TYPE

        raise NotImplementedError("No EVENT_TYPE set")

    def __get_event_values__(self):
        raise NotImplementedError("Class get_values function not implemented")

    def __emit_event__(self):
        assert (
            self.id
        ), "Emitter instance should exist and have an pk assigned before emitting an Event"

        case = self.__get_case__()
        event_type = self.__get_event_type__()

        try:
            Event.objects.get(emitter_id=self.id, type=event_type)
        except Event.DoesNotExist:
            Event.objects.create(emitter=self, type=event_type, case=case)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.__emit_event__()
