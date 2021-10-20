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
        self.skipTest(
            "JudgeView(objection_valid=True), should trigger `is_citizen_objection_valid.value == 'yes_citizen_objection_valid'` and continue with renounce_decision. It doesn't trigger it, but continues with decision-flow instead (Opstellen concept besluit)"
        )
        self.get_case().run_steps(
            *MonitorIncomingView.get_steps(),
            JudgeView(objection_valid=True),  # BUG
            CreateConceptRenounce(),
            CheckRenounceLetter(),
            CreateDefinitiveRenounce(),
            PlanNextStep(),  # TODO not sure about this step, see comment WZ-1635
        )
