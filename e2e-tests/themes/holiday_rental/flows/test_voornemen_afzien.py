from api.config import DecisionType
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.decision import test_nakijken_besluit, test_verwerken_definitieve_besluit
from api.tasks.renounce_decision import (
    task_nakijken_afzien_voornemen,
    test_opstellen_concept_voornemen_afzien,
    test_verwerken_definitieve_voornemen_afzien,
)
from api.test import DefaultAPITest


class TestVoornemenAfzien(DefaultAPITest):
    def test(self):
        """
        This flow only tests one Summon/Decision.
        """
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.HolidayRental.NO_DECISION
            ),
            test_opstellen_concept_voornemen_afzien(),
            task_nakijken_afzien_voornemen(),
            test_verwerken_definitieve_voornemen_afzien(),
            test_uitzetten_vervolgstap(),
        )
