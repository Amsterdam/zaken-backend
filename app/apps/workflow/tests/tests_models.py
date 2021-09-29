from apps.cases.models import Case, CaseReason, CaseTheme
from apps.workflow.models import CaseWorkflow
from django.conf import settings
from django.core import management
from django.test import TestCase
from model_bakery import baker
from SpiffWorkflow.bpmn.specs.BpmnProcessSpec import BpmnProcessSpec
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow


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
        baker.make(CaseWorkflow)
        spec = (
            CaseWorkflow.objects.all()
            .first()
            .get_workflow_spec(
                "top_workflow.bpmn",
                [
                    "common_workflow.bpmn",
                ],
            )
        )
        self.assertEquals(type(spec), BpmnProcessSpec)

    def test_initial_serialized_workflow_state(self):
        """ Tests initial serialized_workflow_state  """
        baker.make(CaseWorkflow)
        workflow_instance = CaseWorkflow.objects.all().first()
        self.assertEquals(workflow_instance._get_serialized_workflow_state(), None)

    def test_get_workflow(self):
        """ Tests get_workflow  """
        baker.make(CaseWorkflow)
        workflow_instance = CaseWorkflow.objects.all().first()
        spec = (
            CaseWorkflow.objects.all()
            .first()
            .get_workflow_spec(
                "top_workflow.bpmn",
                [
                    "common_workflow.bpmn",
                ],
            )
        )
        workflow = workflow_instance.get_workflow(spec)
        self.assertEquals(type(workflow), BpmnWorkflow)

    def test_get_workflow_current_task_names(self):
        """ Tests get workflow current task names  """
        baker.make(CaseWorkflow)
        workflow_instance = CaseWorkflow.objects.all().first()
        spec = (
            CaseWorkflow.objects.all()
            .first()
            .get_workflow_spec(
                "top_workflow.bpmn",
                [
                    "common_workflow.bpmn",
                ],
            )
        )
        workflow = workflow_instance.get_workflow(spec)
        task_names = workflow_instance.get_ready_task_names(workflow)
        self.assertEquals(task_names, ["create_case"])
        task_names = workflow_instance.get_ready_task_names(workflow)
        self.assertEquals(task_names, ["create_case"])

    def test_get_user_task_form(self):
        """ Tests get user task form """
        baker.make(CaseWorkflow)
        workflow_instance = CaseWorkflow.objects.all().first()
        spec = (
            CaseWorkflow.objects.all()
            .first()
            .get_workflow_spec(
                "top_workflow.bpmn",
                [
                    "common_workflow.bpmn",
                ],
            )
        )
        workflow = workflow_instance.get_workflow(spec)
        task_names = workflow_instance.get_ready_task_names(workflow)
        form = workflow_instance.get_user_task_form(task_names[0], workflow)
        self.assertEquals(
            form,
            {
                "form": {"key": "create_case_form"},
                "fields": [
                    {
                        "id": "create_case_formfield",
                        "type": "string",
                        "label": "create_case_formfield label",
                        "default_value": None,
                        "properties": [],
                        "validation": [],
                    }
                ],
            },
        )

    def test_restore_workflow(self):
        """ Tests complete usertask  """
        theme = CaseTheme.objects.create(
            name=settings.DEFAULT_THEME,
        )
        reason = CaseReason.objects.create(
            name=settings.DEFAULT_REASON,
            theme=theme,
        )
        case = Case.objects.create(
            reason=reason,
            theme=theme,
        )
        workflow_instance = CaseWorkflow.objects.create(
            case=case,
        )

        wf = workflow_instance.get_or_restore_workflow_state()
        wfs = workflow_instance.get_serializer().serialize_workflow(wf)

        wf_new = workflow_instance.get_serializer().deserialize_workflow(
            wfs, workflow_spec=workflow_instance.get_workflow_spec()
        )

        wf_new = workflow_instance.get_script_engine(wf=wf_new)
        wf_new.set_data(
            **{
                "status_name": "Huisbzoek",
            }
        )
        wf_new.do_engine_steps()
        wfs_new = workflow_instance.get_serializer().serialize_workflow(wf_new)

        self.assertEquals(wfs, wfs_new)

    def test_set_initial_data_workflow(self):
        """ Tests complete usertask  """
        theme = CaseTheme.objects.create(
            name=settings.DEFAULT_THEME,
        )
        reason = CaseReason.objects.create(
            name=settings.DEFAULT_REASON,
            theme=theme,
        )
        case = Case.objects.create(
            reason=reason,
            theme=theme,
        )
        workflow_instance = CaseWorkflow.objects.create(
            case=case,
        )

        wf = workflow_instance.get_or_restore_workflow_state()

        wf = workflow_instance.get_script_engine(wf)

        wf = workflow_instance.set_initial_data(
            {
                "status_name": "Huisbzoek",
            }
        )

        wfs = workflow_instance.get_serializer().serialize_workflow(wf)

        self.assertEquals(wfs, True)

    # def test_complete_user_task(self):
    #     """ Tests complete usertask  """
    #     theme = CaseTheme.objects.create(
    #         name=settings.DEFAULT_THEME,
    #     )
    #     reason = CaseReason.objects.create(
    #         name=settings.DEFAULT_REASON,
    #         theme=theme,
    #     )
    #     case = Case.objects.create(
    #         reason=reason,
    #         theme=theme,
    #     )
    #     workflow_instance = CaseWorkflow.objects.create(
    #         case=case,
    #     )

    #     workflow = workflow_instance.get_or_restore_workflow_state()
    #     # workflow_instance.set_initial_data(data={
    #     #     "init_data": "my init data",
    #     # }, wf=workflow)

    #     task_names = workflow_instance.get_ready_task_names(workflow)

    #     self.assertEquals(
    #         workflow_instance.get_ready_task_names(workflow), ["create_case"]
    #     )
    #     workflow_instance.complete_user_task(
    #         task_names[0], workflow, {"create_case_formfield": "je moeder"}
    #     )
    #     task_names = workflow_instance.get_ready_task_names(workflow)

    #     self.assertEquals(
    #         workflow_instance.get_ready_task_names(workflow), ["create_case2"]
    #     )
    #     self.assertEquals(CaseUserTask.objects.all().count(), 1)
