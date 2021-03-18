from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class CaseEvent(models.Model):

    TYPE_DEBRIEFING = "DEBRIEFING"
    TYPE_VISIT = "VISIT"
    TYPE_CASE = "CASE"
    TYPE_SUMMON = "SUMMON"
    TYPE_DECISION = "DECISION"
    TYPE_GENERIC_TASK = "GENERIC_TASK"
    TYPES = (
        (TYPE_DEBRIEFING, TYPE_DEBRIEFING),
        (TYPE_VISIT, TYPE_VISIT),
        (TYPE_CASE, TYPE_CASE),
        (TYPE_SUMMON, TYPE_SUMMON),
        (TYPE_GENERIC_TASK, TYPE_GENERIC_TASK),
    )

    date_created = models.DateTimeField(auto_now_add=True)
    case = models.ForeignKey(
        to="cases.Case",
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
        Returns a dictionary with event values retrieved from Emitter object
        """
        event_values = self.emitter.__get_event_values__()
        return event_values

    def __str__(self):
        return f"{self.case.id} Case - Event {self.id} - {self.date_created}"

    class Meta:
        ordering = ["-date_created"]


class ModelEventEmitter(models.Model):
    EVENT_TYPE = None

    class Meta:
        abstract = True

    case = None
    event = GenericRelation(
        CaseEvent, content_type_field="emitter_type", object_id_field="emitter_id"
    )

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
            CaseEvent.objects.get(emitter_id=self.id, type=event_type)
        except CaseEvent.DoesNotExist:
            CaseEvent.objects.create(emitter=self, type=event_type, case=case)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.__emit_event__()
