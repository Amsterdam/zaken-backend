import unittest

from api.client import Client
from api.config import SummonTypes, Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import (
    CheckNotices,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    MonitorIncomingPermitRequest,
    ProcessNotice,
    ScheduleVisit,
    Visit,
)
from api.validators import ValidateOpenTasks


class TestViolationLegalizationLetter(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            ValidateOpenTasks(
                [
                    CreateFindingsReport,
                    CreatePictureReport,
                    CreateConceptNotices,
                ]
            ),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER),
            ValidateOpenTasks([MonitorIncomingPermitRequest]),
        ]

        case.run_steps(steps)
