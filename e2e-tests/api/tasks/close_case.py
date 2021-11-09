import logging

from api import events
from api.config import CloseReason, NextStep
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.decision import SendTaxCollection

logger = logging.getLogger("api")


class PlanNextStep(GenericUserTask):
    asynchronous = True
    task_name = "task_set_next_step"
    description = "Uitzetten vervolgstap"

    def __init__(self, next_step=NextStep.CLOSE):
        data = {"next_step": {"value": next_step}}
        super(PlanNextStep, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [*SendTaxCollection.get_steps(), __class__(next_step=NextStep.CLOSE)]


class Close(AbstractUserTask):
    event = events.CloseEvent
    endpoint = "case-close"
    task_name = "task_close_case"
    description = "Afsluiten zaak"

    def __init__(
        self, reason=CloseReason.HolidayRental.NO_FROUD, description="Some description"
    ):
        super(Close, self).__init__(reason=reason, description=description)

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "theme": case.data["theme"],
            "case_user_task_id": task["case_user_task_id"],
        }

    @staticmethod
    def get_steps():
        return [*PlanNextStep.get_steps(), __class__()]
