import logging

from api import events
from api.config import CloseReason, NextStep
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.decision import test_versturen_invordering_belastingen
from api.user_tasks import task_afsluiten_zaak, task_uitzetten_vervolgstap

logger = logging.getLogger(__name__)


class test_uitzetten_vervolgstap(GenericUserTask, task_uitzetten_vervolgstap):
    def __init__(self, next_step=NextStep.CLOSE):
        data = {"next_step": {"value": next_step}}
        super(test_uitzetten_vervolgstap, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [
            *test_versturen_invordering_belastingen.get_steps(),
            __class__(next_step=NextStep.CLOSE),
        ]


class test_afsluiten_zaak(AbstractUserTask, task_afsluiten_zaak):
    event = events.CloseEvent
    endpoint = "case-close"

    def __init__(
        self, reason=CloseReason.HolidayRental.NO_FROUD, description="Some description"
    ):
        super(test_afsluiten_zaak, self).__init__(
            reason=reason, description=description
        )

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "theme": case.data["theme"],
            "case_user_task_id": task["case_user_task_id"],
        }

    @staticmethod
    def get_steps():
        return [*test_uitzetten_vervolgstap.get_steps(), __class__()]
