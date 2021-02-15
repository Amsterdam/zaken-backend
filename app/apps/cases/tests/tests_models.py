from datetime import datetime, timezone
from uuid import UUID

from apps.cases.models import Case, CaseReason, CaseTeam
from django.core import management
from django.test import TestCase
from freezegun import freeze_time
from model_bakery import baker

# TODO: Tests for CaseState
# TODO: Tests for CaseStateType


class CaseTeamModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_team(self):
        """ Tests TeamModel object creation """
        self.assertEquals(CaseTeam.objects.count(), 0)

        baker.make(CaseTeam)

        self.assertEquals(CaseTeam.objects.count(), 1)


class CaseReasonModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_reason(self):
        """ Tests CaseReason object creation """
        self.assertEquals(CaseTeam.objects.count(), 0)

        baker.make(CaseReason)

        self.assertEquals(CaseReason.objects.count(), 1)

    def test_teams_has_multiple_reasons(self):
        """ Tests reverse access of case reasons through the team object """
        team = baker.make(CaseTeam)
        baker.make(CaseReason, team=team, _quantity=2)

        self.assertEquals(team.reasons.count(), 2)


class CaseModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_case(self):
        """ A case can be created """
        self.assertEquals(Case.objects.count(), 0)

        baker.make(Case)

        self.assertEquals(Case.objects.count(), 1)

    def test_create_case_with_identification(self):
        """ A case can be created with a given identification """
        IDENTIFICATION = "FOO ID"

        case = baker.make(Case, identification=IDENTIFICATION)

        self.assertEquals(IDENTIFICATION, case.identification)

    def test_create_case_has_valid_automatic_identification(self):
        """ When a case is created without an identification, it should have a valid UUID """
        case = baker.make(Case)
        UUID(case.identification, version=4)

    def test_case_initial_state(self):
        """ A case always starts with an initial state """
        case = baker.make(Case)
        self.assertIsNotNone(case.get_current_state())
        self.assertEquals(len(case.case_states.all()), 1)

    @freeze_time("2019-12-25")
    def test_auto_start_date(self):
        """ If a start data isn't specified, it should be set to the current time """
        case = baker.make(Case)
        self.assertEquals(case.start_date, datetime(2019, 12, 25, tzinfo=timezone.utc))

    @freeze_time("2019-12-25")
    def test_set_start_date(self):
        """ If a start data is specified, it should be set to correctly """
        date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        case = baker.make(Case, start_date=date)

        self.assertEquals(case.start_date, date)
