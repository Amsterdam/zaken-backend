from apps.cases.models import Case
from apps.workflow.models import CaseWorkflow
from django.core import management
from django.test import TestCase
from model_bakery import baker
from SpiffWorkflow.bpmn.specs.BpmnProcessSpec import BpmnProcessSpec


class WorkflowModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_workflow(self):
        """ Tests CaseWorkflow object creation """
        self.assertEquals(CaseWorkflow.objects.count(), 0)
        baker.make(CaseWorkflow)
        self.assertEquals(CaseWorkflow.objects.count(), 1)

    def test_can_get_workflow_spec(self):
        """ Tests can get workflow spec """
        case = baker.make(Case)
        workflow = baker.make(
            CaseWorkflow,
            case=case,
            workflow_theme_name="default",
            workflow_version=None,
        )
        self.assertEquals(workflow.get_workflow_spec().__class__, BpmnProcessSpec)
