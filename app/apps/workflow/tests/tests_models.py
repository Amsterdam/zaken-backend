from apps.cases.models import Case, CaseTheme
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from apps.workflow.models import CaseWorkflow
from django.conf import settings
from django.core import management
from django.test import TestCase
from model_bakery import baker
from SpiffWorkflow.bpmn.specs.BpmnProcessSpec import BpmnProcessSpec


class WorkflowModelTest(ZakenBackendTestMixin, TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_can_create_workflow(self):
        """Tests CaseWorkflow object creation"""

        self.assertEquals(CaseWorkflow.objects.count(), 0)
        theme = baker.make(CaseTheme, name=settings.DEFAULT_THEME)
        case = baker.make(Case, theme=theme)
        baker.make(
            CaseWorkflow,
            case=case,
            workflow_version=None,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
        )
        self.assertEquals(CaseWorkflow.objects.count(), 1)

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

        self.assertEquals(workflow.get_workflow_spec().__class__, BpmnProcessSpec)
