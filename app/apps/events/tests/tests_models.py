"""
Tests for CaseEvent & EventsEmitter models
"""

from apps.events.models import CaseEvent
from apps.events.tests.tests_helpers import CaseEventEmitterTestCase
from apps.openzaak.tests.utils import ZakenBackendTestMixin


class CaseEventTest(ZakenBackendTestMixin, CaseEventEmitterTestCase):
    def test_case_creates_events(self):
        """Creating a new EventEmitter should also create corresponding event"""
        self.assertEqual(0, CaseEvent.objects.count())

        self.create_case()

        self.assertEqual(1, CaseEvent.objects.count())

    def test_event_emitter_creates_events(self):
        """Creating a new EventEmitter should also create corresponding event"""
        self.assertEqual(0, CaseEvent.objects.count())

        case = self.create_case()
        CaseEventTest.SubclassEventEmitter.objects.create(case=case)

        # A case (which is needed for any emitter always creates an events. That's why the final counts is 2)
        self.assertEqual(2, CaseEvent.objects.count())

    def test_bad_event_emitter(self):
        """A subclassed EventEmitter that is not configured properly should throw an error"""
        self.assertEqual(0, CaseEvent.objects.count())

        with self.assertRaises(Exception):
            CaseEventTest.SubclassEmptyEventEmitter.objects.create()

        self.assertEqual(0, CaseEvent.objects.count())
