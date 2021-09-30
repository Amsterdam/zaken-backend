from apps.cases.signals import close_case, complete_citizen_report_task
from django.db.models import signals
from django.test import TestCase


class CaseSignalsTest(TestCase):
    def __get_registered_functions__(self):
        """Returns all receiver functions for post_save functions"""
        return [receiver[1]() for receiver in signals.post_save.receivers]

    def test_citizen_report_connected(self):
        """Tests if the citizen_report is registered"""
        registered_functions = self.__get_registered_functions__()
        self.assertIn(complete_citizen_report_task, registered_functions)

    def test_close_case_connected(self):
        """Tests if the close_case is registered"""
        registered_functions = self.__get_registered_functions__()
        self.assertIn(close_case, registered_functions)
