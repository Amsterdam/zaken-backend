from apps.cases.models import Case
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class EventValue:
    """
    Simple data structure to ensure the event values are flat dictionaries
    """

    def __init__(self, key, value):
        assert isinstance(key, str), "key should be a string"
        assert isinstance(value, str), "value should be a string"
        self.key = key
        self.value = value


class Event(models.Model):
    TYPE_DEBRIEFING = "DEBRIEFING"
    TYPES = ((TYPE_DEBRIEFING, TYPE_DEBRIEFING),)

    date_created = models.DateTimeField(auto_now_add=True)
    case = models.ForeignKey(
        to=Case,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="events",
    )
    type = models.CharField(max_length=250, null=False, blank=False, choices=TYPES)
    emitter_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    emitter_id = models.PositiveIntegerField()
    emitter = GenericForeignKey("emitter_type", "emitter_id")

    @property
    def values(self):
        """
        Returns a dictionary with EventValues
        """
        event_values = self.emitter.__get_event_values__()
        values = {}
        for event_value in event_values:
            values[event_value.key] = event_value.value

        return values


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

    def __validate_event_values__(self):
        event_values = self.__get_event_values__()

        for event_value in event_values:
            assert isinstance(
                event_value, EventValue
            ), "Event value should be an EventValue object"

        return True

    def __emit_event__(self):
        assert (
            self.id
        ), "Emitter instance should exist and have an pk assigned before emitting an Event"

        self.__validate_event_values__()
        case = self.__get_case__()
        event_type = self.__get_event_type__()
        events = Event.objects.filter(emitter_id=self.id, type=event_type)

        if not events.count():
            Event.objects.create(emitter=self, type=event_type, case=case)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.__emit_event__()
