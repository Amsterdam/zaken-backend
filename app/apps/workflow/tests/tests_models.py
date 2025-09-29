from apps.cases.models import Case, CaseTheme
from apps.workflow.models import CaseWorkflow
from django.conf import settings
from django.core import management
from django.test import TestCase
from model_bakery import baker
from SpiffWorkflow.bpmn.specs import BpmnProcessSpec


class WorkflowModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_workflow(self):
        """Tests CaseWorkflow object creation"""

        self.assertEqual(CaseWorkflow.objects.count(), 0)
        theme = baker.make(CaseTheme, name=settings.DEFAULT_THEME)
        case = baker.make(Case, theme=theme)
        baker.make(
            CaseWorkflow,
            case=case,
            workflow_version=None,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
        )
        self.assertEqual(CaseWorkflow.objects.count(), 1)

    def test_can_get_workflow_spec(self):
        """Tests can get workflow spec"""

        theme = baker.make(CaseTheme, name=settings.DEFAULT_THEME)
        case = baker.make(Case, theme=theme)
        workflow = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
            id=8,
            workflow_version="0.1.0",
            workflow_theme_name="default",
            data={},
        )

        self.assertEqual(workflow.get_workflow_spec().__class__, BpmnProcessSpec)

    def test_get_workflow_exclude_options(self):
        """Tests can get workflow spec"""

        theme = baker.make(CaseTheme, name=settings.DEFAULT_THEME)
        case = baker.make(Case, theme=theme)
        workflow = baker.make(
            CaseWorkflow,
            case=case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_SUMMON,
            id=8,
            workflow_version="7.1.0",
            workflow_theme_name="default",
            data={},
        )
        exclude_options = workflow.get_workflow_exclude_options()
        self.assertEqual(
            exclude_options,
            ["informatiebrief", "geen_zienswijze"],
            "Should exclude 'informatiebrief' and 'geen_zienswijze' for version 7.1.0",
        )

        # Test case for version 6.0.0
        workflow.workflow_version = "6.0.0"
        exclude_options = workflow.get_workflow_exclude_options()
        self.assertEqual(
            exclude_options,
            ["besluit", "informatiebrief", "geen_zienswijze"],
            "Should exclude 'besluit', 'informatiebrief' and 'geen_zienswijze' for version below 6.3.0",
        )

        # Test case for version 6.3.0
        workflow.workflow_version = "6.3.0"
        exclude_options = workflow.get_workflow_exclude_options()
        self.assertEqual(
            exclude_options,
            ["informatiebrief", "geen_zienswijze"],
            "Should exclude 'informatiebrief' and 'geen_zienswijze' for version 6.3.0",
        )

        # Test case for version 7.2.0
        workflow.workflow_version = "7.2.0"
        exclude_options = workflow.get_workflow_exclude_options()
        self.assertEqual(
            exclude_options,
            ["geen_zienswijze"],
            "Should exclude 'geen_zienswijze' for version 7.2.0",
        )

        # Test case for version 7.3.0 and above (e.g., 7.3.0)
        workflow.workflow_version = "7.3.0"
        exclude_options = workflow.get_workflow_exclude_options()
        self.assertEqual(
            exclude_options,
            [],
            "Should not exclude any options for version 7.3.0 and above",
        )
