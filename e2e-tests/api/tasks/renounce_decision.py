import logging

from api.config import DecisionType
from api.tasks import GenericUserTask
from api.tasks.decision import test_verwerken_definitieve_besluit
from api.user_tasks import (
    task_nakijken_afzien_voornemen,
    task_opstellen_concept_voornemen_afzien,
    task_verwerken_definitieve_voornemen_afzien,
)

logger = logging.getLogger(__name__)


class test_opstellen_concept_voornemen_afzien(
    GenericUserTask, task_opstellen_concept_voornemen_afzien
):
    @staticmethod
    def get_steps():
        return [
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.Vakantieverhuur.NO_DECISION
            ),
            __class__(),
        ]


# TODO improve name
class test_nakijken_afzien_voornemen(GenericUserTask, task_nakijken_afzien_voornemen):
    @staticmethod
    def get_steps():
        return [*test_opstellen_concept_voornemen_afzien.get_steps(), __class__()]


class test_verwerken_definitieve_voornemen_afzien(
    GenericUserTask, task_verwerken_definitieve_voornemen_afzien
):
    description = "Verwerken definitief voornemen afzien"

    @staticmethod
    def get_steps():
        return [*test_nakijken_afzien_voornemen.get_steps(), __class__()]
