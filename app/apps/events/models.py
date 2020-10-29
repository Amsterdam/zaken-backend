from apps.cases.models import Case
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Event(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    case = models.ForeignKey(
        to=Case,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="events",
    )
    type = models.CharField(max_length=250, null=False, blank=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    @property
    def values(self):
        return self.content_object.__get_event_values__()


class EventEmitter(models.Model):
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

        raise NotImplementedError("Class EVENT_TYPE not set")

    def __get_event_values__(self):
        raise NotImplementedError("Class get_values function not implemented")

    def __validate_event_values__(self):
        # TODO: Validate the event values are in the correct data structure (flat key value pair)
        return True

    def __emit_event__(self):
        self.__validate_event_values__()
        case = self.__get_case__()
        event_type = self.__get_event_type__()
        events = Event.objects.filter(object_id=self.id, type=event_type)

        if not events.count():
            Event.objects.create(content_object=self, type=event_type, case=case)

    def save(self, *args, **kwargs):
        self.__emit_event__()
        super().save(*args, **kwargs)
