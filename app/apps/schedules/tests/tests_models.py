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
            baker.make(self.MODEL, name=model_object.name, team=model_object.team)


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
            baker.make(self.MODEL, name=model_object.name, team=model_object.team)


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
            baker.make(self.MODEL, name=model_object.name, team=model_object.team)


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
            baker.make(self.MODEL, name=model_object.name, team=model_object.team)


class ScheduleModelTest(TestCase):
    MODEL = Schedule

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_object(self):
        self.assertEquals(self.MODEL.objects.count(), 0)

        baker.make(self.MODEL)

        self.assertEquals(self.MODEL.objects.count(), 1)

    def test_assert_unique_together(self):
        model_object = baker.make(self.MODEL)

        with self.assertRaises(Exception):
            baker.make(self.MODEL, name=model_object.case, team=model_object.action)
