from datetime import date, datetime, timezone
from uuid import UUID

from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTheme
from apps.workflow.models import CaseUserTask, CaseWorkflow
from django.core import management
from django.test import TestCase
from freezegun import freeze_time
from model_bakery import baker


class CaseStateStypeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_state_type(self):
        """ Tests CaseStateType object creation """
        self.assertEquals(CaseStateType.objects.count(), 0)

        baker.make(CaseStateType)

        self.assertEquals(CaseStateType.objects.count(), 1)

    def test_create_duplicate_state_type_fails(self):
        """ Should fail if a duplicate name is used """
        case_state_type = baker.make(CaseStateType)

        with self.assertRaises(Exception):
            baker.make(CaseStateType, name=case_state_type.name)


class CaseStateModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_state(self):
        """ Tests CaseStateType object creation """
        self.assertEquals(CaseState.objects.count(), 0)

        baker.make(CaseState)

        self.assertEquals(CaseStateType.objects.count(), 1)

    @freeze_time("2019-12-25")
    def test_no_start_date(self):
        """ Uses the current date if no start_date is provided """
        case_state = baker.make(CaseState)
        self.assertEquals(case_state.start_date, date(2019, 12, 25))

    @freeze_time("2019-12-25")
    def test_set_start_date(self):
        """ Uses the given start_date """
        mock_date = date(2021, 12, 25)
        case_state = baker.make(CaseState, start_date=mock_date)
        self.assertEquals(case_state.start_date, mock_date)

    @freeze_time("2019-12-25")
    def test_no_end_date(self):
        """ end_date is none, if not provided """
        case_state = baker.make(CaseState)
        self.assertIsNone(case_state.end_date)

    @freeze_time("2019-12-25")
    def test_end_date(self):
        """ end_state function sets the end_date to the current date """
        case_state = baker.make(CaseState)
        case_state.end_state()
        self.assertEquals(case_state.end_date, date(2019, 12, 25))


class CaseThemeModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_theme(self):
        """ Tests ThemeModel object creation """
        self.assertEquals(CaseTheme.objects.count(), 0)

        baker.make(CaseTheme)

        self.assertEquals(CaseTheme.objects.count(), 1)


class CaseReasonModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_reason(self):
        """ Tests CaseReason object creation """
        self.assertEquals(CaseTheme.objects.count(), 0)

        baker.make(CaseReason)

        self.assertEquals(CaseReason.objects.count(), 1)

    def test_themes_has_multiple_reasons(self):
        """ Tests reverse access of case reasons through the theme object """
        theme = baker.make(CaseTheme)
        baker.make(CaseReason, theme=theme, _quantity=2)

        self.assertEquals(theme.reasons.count(), 2)


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

    def test_set_state(self):
        """ set_state function creates a state with the given name """
        self.assertEqual(CaseState.objects.count(), 0)
        STATE_TYPE_NAME = "MOCK_STATE_TYPE"
        case = baker.make(Case)
        workflow = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=1,
        )
        case.set_state(STATE_TYPE_NAME, workflow=workflow)
        self.assertEqual(CaseState.objects.count(), 1)

    def test_set_state_type(self):
        """
        set_state creates a state type if it doesn't exist yet
        """
        self.assertEqual(CaseStateType.objects.count(), 0)
        STATE_TYPE_NAME = "MOCK_STATE_TYPE"
        case = baker.make(Case)
        workflow = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=2,
        )
        case.set_state(STATE_TYPE_NAME, workflow=workflow)
        self.assertEqual(CaseStateType.objects.count(), 1)

    def test_set_state_type_duplicate(self):
        """
        only one state type can exist after calling set_state twice with the same state type
        """
        self.assertEqual(CaseStateType.objects.count(), 0)
        STATE_TYPE_NAME = "MOCK_STATE_TYPE"
        case = baker.make(Case)
        workflow = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=3,
        )
        case.set_state(STATE_TYPE_NAME, workflow=workflow)
        case.set_state(STATE_TYPE_NAME, workflow=workflow)
        self.assertEqual(CaseStateType.objects.count(), 1)

    def test_get_open_states(self):
        """
        get_current_states returns open states
        """
        STATE_TYPE_NAME_A = "MOCK_STATE_TYPE_A"
        STATE_TYPE_NAME_B = "MOCK_STATE_TYPE_B"

        case = baker.make(Case)
        workflow_a = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=4,
        )
        workflow_b = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=5,
        )
        baker.make(CaseUserTask, workflow=workflow_a, completed=False)
        baker.make(CaseUserTask, workflow=workflow_b, completed=False)
        state_a = case.set_state(STATE_TYPE_NAME_A, workflow=workflow_a)
        state_b = case.set_state(STATE_TYPE_NAME_B, workflow=workflow_b)

        open_state_ids = []
        for open_state in case.get_current_states():
            open_state_ids.append(open_state.id)

        self.assertListEqual(open_state_ids, [state_b.id, state_a.id])

    def test_get_only_open_states(self):
        """
        get_current_states returns no closed states
        """
        STATE_TYPE_NAME_A = "MOCK_STATE_TYPE_A"
        STATE_TYPE_NAME_B = "MOCK_STATE_TYPE_B"
        STATE_TYPE_NAME_C = "MOCK_STATE_TYPE_C"

        case = baker.make(Case)

        workflow_a = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=6,
        )
        workflow_b = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=7,
        )
        baker.make(CaseUserTask, workflow=workflow_a, completed=False)
        baker.make(CaseUserTask, workflow=workflow_b, completed=False)
        state_b = case.set_state(STATE_TYPE_NAME_B, workflow=workflow_a)
        state_a = case.set_state(STATE_TYPE_NAME_A, workflow=workflow_a)
        state_c = case.set_state(STATE_TYPE_NAME_C, workflow=workflow_b)

        state_b.end_state()
        state_b.save()

        open_state_ids = []
        for open_state in case.get_current_states():
            open_state_ids.append(open_state.id)
        self.assertListEqual(open_state_ids, [state_c.id, state_a.id])
