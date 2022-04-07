from datetime import date
from uuid import UUID

from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTheme
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from django.core import management
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker


class CaseStateStypeModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_state_type(self):
        """Tests CaseStateType object creation"""
        self.assertEquals(CaseStateType.objects.count(), 0)

        baker.make(CaseStateType)

        self.assertEquals(CaseStateType.objects.count(), 1)


class CaseStateModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    @freeze_time("2021-12-25")
    def test_set_start_date(self):
        """Uses the given start_date"""
        mock_date = timezone.now()
        case_state = baker.make(CaseState)
        self.assertEquals(case_state.created, mock_date)


class CaseThemeModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_theme(self):
        """Tests ThemeModel object creation"""
        self.assertEquals(CaseTheme.objects.count(), 0)

        baker.make(CaseTheme)

        self.assertEquals(CaseTheme.objects.count(), 1)


class CaseReasonModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_reason(self):
        """Tests CaseReason object creation"""
        self.assertEquals(CaseTheme.objects.count(), 0)

        baker.make(CaseReason)

        self.assertEquals(CaseReason.objects.count(), 1)

    def test_themes_has_multiple_reasons(self):
        """Tests reverse access of case reasons through the theme object"""
        theme = baker.make(CaseTheme)
        baker.make(CaseReason, theme=theme, _quantity=2)

        self.assertEquals(theme.reasons.count(), 2)


class CaseModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_case(self):
        """A case can be created"""
        self.assertEquals(Case.objects.count(), 0)

        baker.make(Case)

        self.assertEquals(Case.objects.count(), 1)

    def test_create_case_with_identification(self):
        """A case can be created with a given identification"""
        IDENTIFICATION = "FOO ID"

        case = baker.make(Case, identification=IDENTIFICATION)

        self.assertEquals(IDENTIFICATION, case.identification)

    def test_create_case_has_valid_automatic_identification(self):
        """When a case is created without an identification, it should have a valid UUID"""
        case = baker.make(Case)
        UUID(case.identification, version=4)

    @freeze_time("2019-12-25")
    def test_auto_start_date(self):
        """If a start data isn't specified, it should be set to the current time"""
        case = baker.make(Case)
        self.assertEquals(case.start_date, date(2019, 12, 25))

    @freeze_time("2019-12-25")
    def test_set_start_date(self):
        """If a start data is specified, it should be set to correctly"""
        start_date = date(2020, 1, 1)
        case = baker.make(Case, start_date=start_date)

        self.assertEquals(case.start_date, start_date)
