from apps.cases.models import Case
from apps.events.models import Event, EventValue, ModelEventEmitter
from django.core import management
from django.db import connection, models
from django.db.models.base import ModelBase
from django.db.utils import ProgrammingError
from rest_framework.test import APITestCase


class EventEmitterTestCase(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def create_case(self):
        case = Case.objects.create()
        return case

    @classmethod
    def setUpClass(cls):
        class SubclassEventEmitter(ModelEventEmitter):
            """ An example EventEmitter subclass used for test purposes"""

            EVENT_TYPE = Event.TYPE_DEBRIEFING
            case = models.ForeignKey(to=Case, null=False, on_delete=models.CASCADE)

            def __get_event_values__(self):
                return [EventValue("foo_text", "hello"), EventValue("foo_number", "1")]

        cls.SubclassEventEmitter = SubclassEventEmitter

        class SubclassEmptyEventEmitter(ModelEventEmitter):
            """ An faulty example of an EventEmitter subclass used for test purposes"""

            EVENT_TYPE = None
            case = None

        cls.SubclassEventEmitter = SubclassEventEmitter
        cls.SubclassEmptyEventEmitter = SubclassEmptyEventEmitter

        try:
            # we create our models "on the fly" in our test db
            with connection.schema_editor() as editor:
                editor.create_model(SubclassEventEmitter)
                editor.create_model(SubclassEmptyEventEmitter)
        except ProgrammingError:
            # The testing models already exist, so don't do anything
            pass

        super(EventEmitterTestCase, cls).setUpClass()
