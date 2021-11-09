import logging

from api.config import Violation
from api.tasks import GenericUserTask
from api.tasks.debrief import Debrief

logger = logging.getLogger("api")


# TODO: as of 20-10-2021 FeedbackReporters is not implemented yet
class FeedbackReporters(GenericUserTask):
    task_name = None  # "task_feedback_reporter"
    description = "Terugkoppelen melder(s)"
    event = None

    def is_ready(self, client, case):
        return True

    def run(self, client, case):
        pass

    @staticmethod
    def get_steps():
        """
        Weird one, because it's dependent on timer.
        """
        return [*Debrief(violation=Violation.YES), __class__()]
