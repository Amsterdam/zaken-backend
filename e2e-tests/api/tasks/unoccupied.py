import logging

from api.config import Violation
from api.tasks import AbstractUserTask
from api.user_tasks import task_opstellen_aanschrijving_eigenaar, task_verwerken_debrief

logger = logging.getLogger(__name__)


class test_opstellen_aanschrijving_eigenaar(
    AbstractUserTask, task_opstellen_aanschrijving_eigenaar
):
    @staticmethod
    def get_steps():
        return [*task_verwerken_debrief.get_steps(violation=Violation.YES), __class__()]
