from apps.summons.signals import (
    create_summon_instance_in_camunda,
    create_summon_instance_in_openzaak,
)
from django.core import management
from django.db.models import signals
from django.test import TestCase


class CaseSignalsTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def __get_registered_functions__(self):
        """ Returns all receiver functions for post_save functions """
        return [receiver[1]() for receiver in signals.post_save.receivers]

    def test_camunda_signal_connected(self):
        """ Tests if the camunda signal is registered """
        registered_functions = self.__get_registered_functions__()
        self.assertIn(create_summon_instance_in_camunda, registered_functions)

    def test_open_zaak_signal_connected(self):
        """ Tests if the openzaak signal is registered """
        registered_functions = self.__get_registered_functions__()
        self.assertIn(create_summon_instance_in_openzaak, registered_functions)
