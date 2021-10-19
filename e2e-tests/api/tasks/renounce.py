import logging

from api.config import DecisionType
from api.tasks import GenericUserTask
from api.tasks.decision import Decision

logger = logging.getLogger("api")


class CreateConceptRenounce(GenericUserTask):
    task_name = "task_create_concept_renounce"
    description = "Opstellen concept voornemen afzien"

    @staticmethod
    def get_steps():
        return [
            *Decision.get_steps(type=DecisionType.HolidayRental.NO_DECISION),
            __class__(),
        ]


class CheckRenounceLetter(GenericUserTask):
    task_name = "task_check_renounce_letter"
    description = "Nakijken brief"

    @staticmethod
    def get_steps():
        return [*CreateConceptRenounce.get_steps(), __class__()]


class CreateDefinitiveRenounce(GenericUserTask):
    task_name = "task_create_definitive_renounce"
    description = "Verwerken definitief voornemen afzien"

    @staticmethod
    def get_steps():
        return [*CheckRenounceLetter.get_steps(), __class__()]
