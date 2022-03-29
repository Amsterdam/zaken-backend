import logging

from api import events
from api.config import CloseReason, NextStep
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.debrief import test_opstellen_verkorte_rapportage_huisbezoek
from api.user_tasks import (
    task_close_case,
    task_close_case_concept,
    task_uitzetten_vervolgstap,
)

logger = logging.getLogger(__name__)


class test_uitzetten_vervolgstap(GenericUserTask, task_uitzetten_vervolgstap):
    def __init__(self, next_step=NextStep.CLOSE):
        super().__init__(next_step={"value": next_step})

    @staticmethod
    def get_steps(next_step=NextStep.CLOSE):
        return [
            *test_opstellen_verkorte_rapportage_huisbezoek.get_steps(),  # shortest path
            __class__(next_step=next_step),
        ]


class test_close_case_concept(GenericUserTask, task_close_case_concept):
    def __init__(self, sluiten_zaak_keuze="direct_resultaat_boeken"):
        super().__init__(sluiten_zaak_keuze={"value": sluiten_zaak_keuze})

    @staticmethod
    def get_steps(sluiten_zaak_keuze="direct_resultaat_boeken"):
        return [
            *test_uitzetten_vervolgstap.get_steps(),  # shortest path
            __class__(sluiten_zaak_keuze=sluiten_zaak_keuze),
        ]


class test_close_case(AbstractUserTask, task_close_case):
    event = events.CloseEvent
    endpoint = "case-close"

    def __init__(
        self,
        reason=CloseReason.Vakantieverhuur.NO_FROUD,
        description="Some description",
    ):
        super().__init__(reason=reason, description=description)

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "theme_id": case.data["theme"],
            "case_user_task_id": task["case_user_task_id"],
        }

    @staticmethod
    def get_steps():
        return [*test_uitzetten_vervolgstap.get_steps(), __class__()]
