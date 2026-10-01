from datetime import date
from uuid import UUID

from apps.addresses.models import Address
from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTheme
from django.core import management
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker


class CaseStateStypeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_state_type(self):
        """Tests CaseStateType object creation"""
        self.assertEqual(CaseStateType.objects.count(), 0)

        baker.make(CaseStateType)

        self.assertEqual(CaseStateType.objects.count(), 1)


class CaseStateModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    @freeze_time("2021-12-25")
    def test_set_start_date(self):
        """Uses the given start_date"""
        mock_date = timezone.now()
        case_state = baker.make(CaseState)
        self.assertEqual(case_state.created, mock_date)


class CaseThemeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_theme(self):
        """Tests ThemeModel object creation"""
        self.assertEqual(CaseTheme.objects.count(), 0)

        baker.make(CaseTheme)

        self.assertEqual(CaseTheme.objects.count(), 1)


class CaseReasonModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_reason(self):
        """Tests CaseReason object creation"""
        self.assertEqual(CaseTheme.objects.count(), 0)

        baker.make(CaseReason)

        self.assertEqual(CaseReason.objects.count(), 1)

    def test_themes_has_multiple_reasons(self):
        """Tests reverse access of case reasons through the theme object"""
        theme = baker.make(CaseTheme)
        baker.make(CaseReason, theme=theme, _quantity=2)

        self.assertEqual(theme.reasons.count(), 2)


class CaseModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_case(self):
        """A case can be created"""
        self.assertEqual(Case.objects.count(), 0)

        baker.make(Case)

        self.assertEqual(Case.objects.count(), 1)

    def test_create_case_with_identification(self):
        """A case can be created with a given identification"""
        IDENTIFICATION = "FOO ID"

        case = baker.make(Case, identification=IDENTIFICATION)

        self.assertEqual(IDENTIFICATION, case.identification)

    def test_create_case_has_valid_automatic_identification(self):
        """When a case is created without an identification, it should have a valid UUID"""
        case = baker.make(Case)
        UUID(case.identification, version=4)

    @freeze_time("2019-12-25")
    def test_auto_start_date(self):
        """If a start data isn't specified, it should be set to the current time"""
        case = baker.make(Case)
        self.assertEqual(case.start_date, date(2019, 12, 25))

    @freeze_time("2019-12-25")
    def test_set_start_date(self):
        """If a start data is specified, it should be set to correctly"""
        start_date = date(2020, 1, 1)
        case = baker.make(Case, start_date=start_date)

        self.assertEqual(case.start_date, start_date)


class CaseOpenSensitiveCaseOnAddressTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()
        self.address = baker.make(Address)
        self.theme = baker.make(CaseTheme, sensitive=False)
        self.sensitive_theme = baker.make(CaseTheme, sensitive=True)

    def get_annotated_value(self, case):
        return (
            Case.objects.with_open_sensitive_case_on_address()
            .get(pk=case.pk)
            .has_open_sensitive_case_on_address
        )

    def test_without_sensitive_case_on_address(self):
        """A case on an address without sensitive cases is not signaled"""
        case = baker.make(Case, address=self.address, theme=self.theme)

        self.assertFalse(self.get_annotated_value(case))

    def test_with_open_sensitive_case_on_address(self):
        """A case on an address with an open sensitive case is signaled"""
        case = baker.make(Case, address=self.address, theme=self.theme)
        baker.make(Case, address=self.address, theme=self.sensitive_theme)

        self.assertTrue(self.get_annotated_value(case))

    def test_with_closed_sensitive_case_on_address(self):
        """A closed sensitive case on the address is not signaled"""
        case = baker.make(Case, address=self.address, theme=self.theme)
        baker.make(
            Case,
            address=self.address,
            theme=self.sensitive_theme,
            end_date=date(2020, 1, 1),
        )

        self.assertFalse(self.get_annotated_value(case))

    def test_with_open_sensitive_case_on_other_address(self):
        """An open sensitive case on another address is not signaled"""
        case = baker.make(Case, address=self.address, theme=self.theme)
        baker.make(Case, address=baker.make(Address), theme=self.sensitive_theme)

        self.assertFalse(self.get_annotated_value(case))

    def test_sensitive_case_is_never_signaled(self):
        """Multiple sensitive cases on the same address do not signal each other"""
        sensitive_case_a = baker.make(
            Case, address=self.address, theme=self.sensitive_theme
        )
        sensitive_case_b = baker.make(
            Case, address=self.address, theme=self.sensitive_theme
        )

        self.assertTrue(sensitive_case_a.sensitive)
        self.assertFalse(self.get_annotated_value(sensitive_case_a))
        self.assertFalse(self.get_annotated_value(sensitive_case_b))
