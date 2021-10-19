import unittest

from api.client import Client
from api.config import DecisionType, SummonTypes, Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import (
    CheckConceptDecision,
    CheckNotices,
    CreateConceptDecision,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    Decision,
    JudgeView,
    MonitorIncomingView,
    ProcessNotice,
    ScheduleVisit,
    SendTaxCollection,
    Visit,
)
from api.validators import AssertNumberOfOpenTasks


class TestInvalidCivilianObjection(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            MonitorIncomingView(),
            JudgeView(objection_valid=False),
            CreateConceptDecision(),
            CheckConceptDecision(),
            Decision(type=DecisionType.HolidayRental.FINE),
            SendTaxCollection(),
            AssertNumberOfOpenTasks(
                0
            ),  # BUG Current implementation in Spiff gives invalid task_contact_city_district
        ]

        case.run_steps(steps)
