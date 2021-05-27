from apps.summons.models import Summon, SummonedPerson, SummonType
from django.core import management
from django.test import TestCase
from model_bakery import baker


class SummonModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_summon(self):
        """ Tests ThemeModel object creation """
        self.assertEquals(Summon.objects.count(), 0)

        baker.make(Summon)

        self.assertEquals(Summon.objects.count(), 1)


class SummonTypeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_summon_type(self):
        """ Tests ThemeModel object creation """
        self.assertEquals(SummonType.objects.count(), 0)

        baker.make(SummonType)

        self.assertEquals(SummonType.objects.count(), 1)


class SummonedPersonTypeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_summoned_person(self):
        """ Tests ThemeModel object creation """
        self.assertEquals(SummonedPerson.objects.count(), 0)

        baker.make(SummonedPerson)

        self.assertEquals(SummonedPerson.objects.count(), 1)
