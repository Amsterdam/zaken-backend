from datetime import datetime, timezone
from uuid import UUID

from apps.cases.models import Case, CaseReason, CaseTeam
from django.test import TestCase
from freezegun import freeze_time


class CaseTeamModelTest(TestCase):
    def test_can_create_team(self):
        """ Tests TeamModel object creation """
        self.assertEquals(CaseTeam.objects.count(), 0)

        CaseTeam.objects.create(name="Foo Case Team")

        self.assertEquals(CaseTeam.objects.count(), 1)


class CaseReasonModelTest(TestCase):
    def test_can_create_reason(self):
        """ Tests CaseReason object creation """
        self.assertEquals(CaseTeam.objects.count(), 0)

        team = CaseTeam.objects.create(name="Foo Case Team")
        CaseReason.objects.create(name="Foo Reason", team=team)

        self.assertEquals(CaseTeam.objects.count(), 1)

    def test_teams_has_multiple_reasons(self):
        """ Tests reverse access of case reasons through the team object """

        team = CaseTeam.objects.create(name="Foo")
        CaseReason.objects.create(name="Foo Reason A", team=team)
        CaseReason.objects.create(name="Foo Reason B", team=team)

        self.assertEquals(team.reasons.count(), 2)


class CaseModelTest(TestCase):
    def test_can_create_case(self):
        """ A case can be created """
        self.assertEquals(Case.objects.count(), 0)

        team = CaseTeam.objects.create(name="Foo Case Team")
        reason = CaseReason.objects.create(name="Foo Reason", team=team)
        Case.objects.create(team=team, reason=reason)

        self.assertEquals(Case.objects.count(), 1)

    def test_create_case_with_identification(self):
        """ A case can be created with a given identification """
        IDENTIFICATION = "FOO ID"
        case = Case.objects.create(identification=IDENTIFICATION)
        self.assertEquals(IDENTIFICATION, case.identification)

    def test_create_case_has_valid_automatic_identification(self):
        """ When a case is created without an identification, it should have a valid UUID """
        case = Case.objects.create()
        UUID(case.identification, version=4)

    @freeze_time("2019-12-25")
    def test_auto_start_date(self):
        """ If a start data isn't specified, it should be set to the current time """
        case = Case.objects.create()
        self.assertEquals(case.start_date, datetime(2019, 12, 25, tzinfo=timezone.utc))

    @freeze_time("2019-12-25")
    def test_set_start_date(self):
        """ If a start data is specified, it should be set to correctly """
        date = datetime(2020, 1, 1, tzinfo=timezone.utc)

        case = Case.objects.create(start_date=date)
        self.assertEquals(case.start_date, date)
