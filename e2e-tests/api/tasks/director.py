import logging

from api.config import Violation
from api.tasks import GenericUserTask
from api.tasks.debrief import test_verwerken_debrief
from api.user_tasks import task_terugkoppelen_melder

logger = logging.getLogger(__name__)


# TODO: as of 20-10-2021 FeedbackReporters is not implemented yet
class test_terugkoppelen_melder(GenericUserTask, task_terugkoppelen_melder):
    event = None

    def is_ready(self, client, case):
        return True

    def run(self, client, case):
        pass

    @staticmethod
    def get_steps():
        return [*test_verwerken_debrief(violation=Violation.YES), __class__()]
