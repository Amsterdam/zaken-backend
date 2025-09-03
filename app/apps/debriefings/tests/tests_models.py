"""
Tests for Debriefing models
"""

from datetime import datetime, timezone

from apps.debriefings.models import Debriefing, ViolationType
from apps.debriefings.tests.tests_helpers import DebriefingTestMixin
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from django.test import TestCase
from freezegun import freeze_time


class DebriefingModelTest(ZakenBackendTestMixin, TestCase, DebriefingTestMixin):
    fixtures = ["fixture.json"]

    def test_can_create_debrief(self):
        self.assertEqual(Debriefing.objects.count(), 0)
        self.create_debriefing()
        self.assertEqual(Debriefing.objects.count(), 1)

    @freeze_time("2019-12-25")
    def test_date_added(self):
        debriefing = self.create_debriefing()

        self.assertEquals(
            debriefing.date_added, datetime(2019, 12, 25, tzinfo=timezone.utc)
        )

    def test_date_modified(self):
        with freeze_time("2019-12-25"):
            debriefing = self.create_debriefing()

            self.assertEquals(
                debriefing.date_modified, datetime(2019, 12, 25, tzinfo=timezone.utc)
            )

        with freeze_time("2019-12-26"):
            debriefing.feedback = "New Feedback"
            debriefing.save()

        self.assertEquals(
            debriefing.date_modified, datetime(2019, 12, 26, tzinfo=timezone.utc)
        )

    @freeze_time("2019-12-25")
    def test_can_be_modified(self):
        debriefing = self.create_debriefing()
        modified_feedback = "Adding other text"
        modified_violation = ViolationType.objects.filter(value="NO").first()
        debriefing.feedback = modified_feedback
        debriefing.violation = modified_violation

        debriefing.save()

        debriefing = Debriefing.objects.all()[0]

        self.assertEquals(debriefing.feedback, modified_feedback)
        self.assertEquals(debriefing.violation, modified_violation)

    def test_debriefing_get_violation_choices(self):
        theme_id = 2
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_RESEARCH_REQUIRED",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))

        theme_id = 3
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_RESEARCH_REQUIRED",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))

        theme_id = 4
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_RESEARCH_REQUIRED",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))

        theme_id = 5
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_RESEARCH_REQUIRED",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
            "LIKELY_INHABITED",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))

        theme_id = 6
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_RESEARCH_REQUIRED",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))

        theme_id = 7
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_RESEARCH_REQUIRED",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))

        theme_id = 8
        expected_values = [
            "NO",
            "YES",
            "ADDITIONAL_VISIT_REQUIRED",
            "ADDITIONAL_VISIT_WITH_AUTHORIZATION",
            "SEND_TO_OTHER_THEME",
            "SERVICE_COSTS",
            "SCHEDULE_CONVERSATION",
            "ADVICE_OTHER_DISCIPLINE",
            "REQUEST_DOCUMENTS",
            "SEND_TO_WOON",
            "SEND_TO_ANOTHER_EXTERNAL_PARTY",
        ]
        result = [
            choice[1] for choice in Debriefing.get_violation_choices_by_theme(theme_id)
        ]
        self.assertEqual(set(result), set(expected_values))
