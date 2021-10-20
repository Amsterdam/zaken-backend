import logging

from api.tasks import GenericUserTask

logger = logging.getLogger("api")


class FeedbackReporters(GenericUserTask):
    task_name = "task_feedback_reporter"
    description = "Terugkoppelen melder(s)"

    @staticmethod
    def get_steps():
        """
        Weird one, because it's dependent on timer.
        """
        return [
            # No preceiding step, case was just created
            __class__()
        ]
