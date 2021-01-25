from apps.cases.signals import (
    create_case_instance_in_camunda,
    create_case_instance_in_openzaak,
)
from django.db.models import signals
from django.test import TestCase


class CaseSignalsTest(TestCase):
    def __get_registered_functions__(self):
        """ Returns all receiver functions for post_save functions """
        return [receiver[1]() for receiver in signals.post_save.receivers]

    def test_camunda_signal_connected(self):
        """ Tests if the camunda signal is registered """
        registered_functions = self.__get_registered_functions__()
        self.assertIn(create_case_instance_in_camunda, registered_functions)

    def test_open_zaak_signal_connected(self):
        """ Tests if the openzaak signal is registered """
        registered_functions = self.__get_registered_functions__()
        self.assertIn(create_case_instance_in_openzaak, registered_functions)
