import logging

from api.tasks import GenericUserTask

logger = logging.getLogger("api")


# TODO: as of 20-10-2021 FeedbackReporters is not implemented yet
class FeedbackReporters(GenericUserTask):
    task_name = None  # "task_feedback_reporter"
    description = "Terugkoppelen melder(s)"

    def is_ready(self, client, case):
        return True

    def run(self, client, case):
        pass

    @staticmethod
    def get_steps():
        """
        Weird one, because it's dependent on timer.
        """
        return [
            # No preceiding step, case was just created
            __class__()
        ]
