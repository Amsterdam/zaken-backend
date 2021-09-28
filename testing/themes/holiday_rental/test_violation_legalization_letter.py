import unittest

from api.client import Client
from api.config import SummonTypes, Themes, api_config
from api.mock import get_case_mock
from api.tasks import (
    AssertNextOpenTasks,
    AssertNumberOfOpenTasks,
    CheckNotices,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    FeedbackReporters,
    ScheduleVisit,
    Summon,
    Task,
    Visit,
)


class TestViolationLegalizationLetter(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = (
            ScheduleVisit(),
            Visit(),
            Debrief(violation="YES"),
            AssertNextOpenTasks(
                [
                    Task.create_findings_report,
                    Task.create_picture_report,
                    Task.create_concept_notices,
                    Task.feedback_reporters
                    if self.api.legacy_mode  # Is this a known bug with Camunda?
                    else None,
                ]
            ),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            AssertNextOpenTasks(
                [
                    Task.check_notices,
                    Task.feedback_reporters
                    if self.api.legacy_mode  # Is this a known bug with Camunda?
                    else None,
                ]
            ),
            CheckNotices(),
            Summon(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER),
            AssertNextOpenTasks([Task.monitor_incoming_permit_request]),
            # TODO test the rest of the process
        )

        case.run_steps(steps)
