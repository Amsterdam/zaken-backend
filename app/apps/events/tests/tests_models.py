"""
Tests for Event & EventsEmitter models
"""
from apps.events.models import Event
from apps.events.tests.tests_helpers import EventEmitterTestCase
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class EventTest(EventEmitterTestCase):
    def test_event_emitter_creates_events(self):
        """ Creating a new EventEmitter should also create corresponding event"""
        self.assertEqual(0, Event.objects.count())

        case = self.create_case()
        EventTest.SubclassEventEmitter.objects.create(case=case)

        self.assertEqual(1, Event.objects.count())

    def test_bad_event_emitter(self):
        """ A subclassed EventEmitter that is not configured properly should throw an error"""
        self.assertEqual(0, Event.objects.count())

        with self.assertRaises(Exception):
            EventTest.SubclassEmptyEventEmitter.objects.create()

        self.assertEqual(0, Event.objects.count())
