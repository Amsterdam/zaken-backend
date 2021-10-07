import unittest

from api.client import Client
from api.config import (
    DecisionType,
    Objection,
    ReviewRequest,
    SummonTypes,
    Themes,
    api_config,
)
from api.mock import get_case_mock
from api.tasks import (
    AssertNextOpenTasks,
    AssertNumberOfOpenTasks,
    CheckDecision,
    CheckIncomingView,
    CheckNotices,
    Close,
    ContactDistrict,
    CreateConceptDecision,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    Decision,
    FeedbackReporters,
    JudgeReopeningRequest,
    JudgeView,
    MonitorIncomingView,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    PlanNextStep,
    Reopen,
    SaveFireBrigadeAdvice,
    ScheduleRecheck,
    ScheduleVisit,
    SendTaxCollection,
    Summon,
    Task,
    Visit,
)


class TestInvalidCivilianObjection(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation="YES"),
            FeedbackReporters() if self.api.legacy_mode else None,  # BUG in Camunda?
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            Summon(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            MonitorIncomingView(objection=True),
            # CheckIncomingView(objection=Objection.YES), # andere test voor maken? Kan dit zonder timer?
            JudgeView(objection_valid=False),
            CreateConceptDecision(),
            CheckDecision(),
            Decision(type=DecisionType.HolidayRental.FINE),
            SendTaxCollection(),
            AssertNumberOfOpenTasks(0)
            if self.api.legacy_mode
            else ContactDistrict(),  # BUG in Spiff
        ]

        case.run_steps(steps)
