"""
Tests for Debriefing models
"""
from datetime import datetime, timezone

from apps.debriefings.models import Debriefing
from apps.debriefings.tests.tests_helpers import DebriefingTestMixin
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from django.test import TestCase
from freezegun import freeze_time


class DebriefingModelTest(ZakenBackendTestMixin, TestCase, DebriefingTestMixin):
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
        modified_violation = Debriefing.VIOLATION_ADDITIONAL_RESEARCH_REQUIRED

        debriefing.feedback = modified_feedback
        debriefing.violation = modified_violation

        debriefing.save()

        debriefing = Debriefing.objects.all()[0]

        self.assertEquals(debriefing.feedback, modified_feedback)
        self.assertEquals(debriefing.violation, modified_violation)
