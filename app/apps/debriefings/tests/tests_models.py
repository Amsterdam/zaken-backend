"""
Tests for Debriefing models
"""
from datetime import datetime

from apps.cases.models import Case
from apps.debriefings.models import Debriefing
from apps.users.models import User
from django.test import TestCase
from freezegun import freeze_time
from pytz import UTC


class DebriefingModelTest(TestCase):
    def create_case(self):
        case = Case.objects.create()
        return case

    def create_user(self):
        USER_EMAIL = "foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)
        return user

    def create_debriefing(self):
        case = self.create_case()
        author = self.create_user()
        violation = True
        feedback = "Feedback text lorem ipsum"

        debriefing = Debriefing.objects.create(
            case=case, author=author, violation=violation, feedback=feedback
        )

        return debriefing

    def test_can_create_debrief(self):
        self.assertEqual(Debriefing.objects.count(), 0)
        self.create_debriefing()
        self.assertEqual(Debriefing.objects.count(), 1)

    @freeze_time("2019-12-25")
    def test_date_added(self):
        debriefing = self.create_debriefing()

        self.assertEquals(debriefing.date_added, datetime(2019, 12, 25))

    def test_date_modified(self):
        with freeze_time("2019-12-25"):
            debriefing = self.create_debriefing()

            self.assertEquals(debriefing.date_modified, datetime(2019, 12, 25))

        with freeze_time("2019-12-26"):
            debriefing.feedback = "New Feedback"
            debriefing.save()

        self.assertEquals(debriefing.date_modified, datetime(2019, 12, 26))

    def test_can_be_modified(self):
        debriefing = self.create_debriefing()
        modified_feedback = debriefing.feedback + "Adding more text"
        modified_violation = not debriefing.violation

        debriefing.feedback = modified_feedback
        debriefing.violation = modified_violation

        debriefing.save()

        debriefing = Debriefing.objects.all()[0]

        self.assertEquals(debriefing.feedback, modified_feedback)
        self.assertEquals(debriefing.violation, modified_violation)
