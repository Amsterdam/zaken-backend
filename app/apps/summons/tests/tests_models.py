from apps.openzaak.tests.utils import ZakenBackendTestMixin
from apps.summons.models import Summon, SummonedPerson, SummonType
from django.core import management
from django.test import TestCase
from model_bakery import baker


class SummonModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_summon(self):
        """Tests ThemeModel object creation"""
        self.assertEqual(Summon.objects.count(), 0)

        baker.make(Summon)

        self.assertEqual(Summon.objects.count(), 1)


class SummonTypeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_summon_type(self):
        """Tests ThemeModel object creation"""
        self.assertEqual(SummonType.objects.count(), 0)

        baker.make(SummonType)

        self.assertEqual(SummonType.objects.count(), 1)


class SummonedPersonTypeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_summoned_person(self):
        """Tests ThemeModel object creation"""
        self.assertEqual(SummonedPerson.objects.count(), 0)

        baker.make(SummonedPerson)

        self.assertEqual(SummonedPerson.objects.count(), 1)
