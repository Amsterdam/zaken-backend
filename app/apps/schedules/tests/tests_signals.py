from apps.schedules.signals import complete_task_create_schedule
from django.core import management
from django.db.models import signals
from django.test import TestCase


class ScheduleSignalsTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def __get_registered_functions__(self):
        """ Returns all receiver functions for post_save functions """
        return [receiver[1]() for receiver in signals.post_save.receivers]

    def test_signal_connected(self):
        """ Tests if the signal is registered """
        registered_functions = self.__get_registered_functions__()
        self.assertIn(complete_task_create_schedule, registered_functions)
