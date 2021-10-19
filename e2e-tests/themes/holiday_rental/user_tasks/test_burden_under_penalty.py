import unittest

from api.client import Client
from api.config import DecisionType, Themes, api_config
from api.mock import get_case_mock
from api.tasks import CheckConceptDecision, Decision, PlanNextStep
from api.validators import AssertOpenTasks


class TestBurdenUnderPenalty(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    """
    In case of BURDEN_UNDER_PENALTY we don't expect SendTaxCollection or ContactDistrict.
    But we do expect PlanNextStep
    """

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.BURDEN_UNDER_PENALTY),
            AssertOpenTasks([PlanNextStep]),
        ]
        case.run_steps(steps)
