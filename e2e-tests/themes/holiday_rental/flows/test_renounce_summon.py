from api.config import ObjectionValid
from api.tasks.close_case import PlanNextStep
from api.tasks.renounce_decision import (
    CheckRenounceLetter,
    CreateConceptRenounce,
    CreateDefinitiveRenounce,
)
from api.tasks.summon import JudgeView, MonitorIncomingView
from api.test import DefaultAPITest


class TestRenounceSummon(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *MonitorIncomingView.get_steps(),
            JudgeView(objection_valid=ObjectionValid.YES),
            CreateConceptRenounce(),
            CheckRenounceLetter(),
            CreateDefinitiveRenounce(),
            PlanNextStep(),
        )
