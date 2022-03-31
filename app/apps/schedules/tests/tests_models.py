from apps.openzaak.tests.utils import ZakenBackendTestMixin
from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from django.core import management
from django.test import TestCase
from model_bakery import baker


class ActionModelTest(TestCase):
    MODEL = Action

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_object(self):
        self.assertEquals(self.MODEL.objects.count(), 0)

        baker.make(self.MODEL)

        self.assertEquals(self.MODEL.objects.count(), 1)

    def test_assert_unique_together(self):
        model_object = baker.make(self.MODEL)

        with self.assertRaises(Exception):
            baker.make(self.MODEL, name=model_object.name, theme=model_object.theme)


class WeekSegmentModelTest(TestCase):
    MODEL = WeekSegment

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_object(self):
        self.assertEquals(self.MODEL.objects.count(), 0)

        baker.make(self.MODEL)

        self.assertEquals(self.MODEL.objects.count(), 1)

    def test_assert_unique_together(self):
        model_object = baker.make(self.MODEL)

        with self.assertRaises(Exception):
            baker.make(self.MODEL, name=model_object.name, theme=model_object.theme)


class DaySegmentModelTest(TestCase):
    MODEL = DaySegment

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_object(self):
        self.assertEquals(self.MODEL.objects.count(), 0)

        baker.make(self.MODEL)

        self.assertEquals(self.MODEL.objects.count(), 1)

    def test_assert_unique_together(self):
        model_object = baker.make(self.MODEL)

        with self.assertRaises(Exception):
            baker.make(self.MODEL, name=model_object.name, theme=model_object.theme)


class PriorityModelTest(TestCase):
    MODEL = Priority

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_object(self):
        self.assertEquals(self.MODEL.objects.count(), 0)

        baker.make(self.MODEL)

        self.assertEquals(self.MODEL.objects.count(), 1)

    def test_assert_unique_together(self):
        model_object = baker.make(self.MODEL)

        with self.assertRaises(Exception):
            baker.make(self.MODEL, name=model_object.name, theme=model_object.theme)


class ScheduleModelTest(ZakenBackendTestMixin, TestCase):
    MODEL = Schedule

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_object(self):
        self.assertEquals(self.MODEL.objects.count(), 0)

        baker.make(self.MODEL)

        self.assertEquals(self.MODEL.objects.count(), 1)

    def test_assert_unique_together(self):
        model_object = baker.make(self.MODEL)

        with self.assertRaises(Exception):
            baker.make(self.MODEL, name=model_object.case, theme=model_object.action)
