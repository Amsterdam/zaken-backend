from api.config import Reason, Theme, VisitNextStep
from api.tasks.debrief import test_verwerken_debrief
from api.tasks.visit import (
    test_aanvragen_machtiging,
    test_bepalen_zaakproces,
    test_inplannen_status,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_bepalen_zaakproces(DefaultAPITest):
    def get_case_data(self):
        return {"theme_id": Theme.ONDERMIJNING, "reason": Reason.Ondermijning.MMA}

    def test_no_visit(self):
        self.get_case().run_steps(
            test_bepalen_zaakproces(visit_next_step=VisitNextStep.NO_VISIT),
            ValidateOpenTasks(test_verwerken_debrief),
        )

    def test_with_authorization(self):
        self.get_case().run_steps(
            test_bepalen_zaakproces(
                visit_next_step=VisitNextStep.VISIT_WITH_AUTHORIZATION
            ),
            ValidateOpenTasks(test_aanvragen_machtiging),
        )

    def test_without_authorization(self):
        self.get_case().run_steps(
            test_bepalen_zaakproces(
                visit_next_step=VisitNextStep.VISIT_WITHOUT_AUTHORIZATION
            ),
            ValidateOpenTasks(test_inplannen_status),
        )
