from apps.cases.models import Case
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.task import Task as SpiffWorkflowTask


def get_workflow_spec_choices():
    return [[k, k] for k, v in settings.WORKFLOWS.items()]


class Workflow(models.Model):
    case = models.ForeignKey(
        to=Case,
        related_name="workflows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    workflow_spec = models.CharField(
        max_length=100,
        choices=get_workflow_spec_choices(),
        default=settings.DEFAULT_WORKFLOW,
    )
    serialized_workflow_state = models.JSONField(null=True)
    wf = None
    serializer = BpmnSerializer
    proccess_conf = settings.WORKFLOWS.get(settings.DEFAULT_WORKFLOW)

    def _get_strip_extensie(self, file_name):
        return file_name.split(".")[0]

    def _task_form_to_python(self, form):
        return {
            "form": {"key": form.key},
            "fields": [f.__dict__ for f in form.fields],
        }

    def get_serializer(self):
        return self.serializer()

    def get_workflow_spec(self, spec_file=None, sub_files=[]):
        x = CamundaParser()
        if spec_file and sub_files:
            for f in sub_files:
                x.add_bpmn_file(f)
            x.add_bpmn_file(spec_file)
            return x.get_spec(self._get_strip_extensie(spec_file))
        else:
            workflow_spec = settings.WORKFLOWS.get(
                self.workflow_spec, settings.DEFAULT_WORKFLOW
            )
            for f in workflow_spec.get("proccess_files"):
                x.add_bpmn_file(f)
            return x.get_spec(workflow_spec.get("main_proccess"))

    def get_script_engine(self, wf):
        case = self.case
        workflow_instance = self

        def set_status(input):
            print("set_status: %s" % input)
            case.set_state(input, workflow_instance)

        wf.script_engine = BpmnScriptEngine(
            scriptingAdditions={
                "set_status": set_status,
            }
        )
        return wf

    def _print_task_data(self, wf):
        print("START: print data")
        print(wf.name)
        if wf.outer_workflow:
            print("outer_workflow")
            print(wf.outer_workflow.name)
        print(wf.script_engine)
        print(wf.dump())
        for t in wf.get_tasks():
            print("-")
            print(t.task_spec.name)
            if hasattr(t.task_spec, "script"):
                print(t.task_spec.script)
            print(t.task_spec.data)
            print(t.data)
        print("END: print data")

    def get_user_task_form(self, task_name):
        ready_tasks = self.wf.get_ready_user_tasks()
        tasks = [t for t in ready_tasks if t.task_spec.name == task_name]
        if not tasks or len(tasks) > 1:
            return {}
        return self._task_form_to_python(tasks[0].task_spec.form)

    def create_user_tasks(self, ready_tasks):
        from string import Template

        task_data = [
            Task(
                task_name_id=task.task_spec.name,
                name=Template(task.task_spec.description).safe_substitute(task.data),
                roles=[r.strip() for r in task.task_spec.lane.split(",")],
                case=self.case,
                workflow=self,
            )
            for task in ready_tasks
        ]

        task_instances = Task.objects.bulk_create(task_data)

        return task_instances

    @staticmethod
    def complete_user_task(task_id, data):
        task = Task.objects.get(id=task_id)
        task.workflow.complete_user_task_and_create_new_user_tasks(
            task.task_name_id, data
        )

    def complete_user_task_and_create_new_user_tasks(self, task_name=None, data=None):
        wf = self.get_or_restore_workflow_state()

        wf.do_engine_steps()
        ready_tasks = wf.get_ready_user_tasks()

        # # complete not UserTasks
        # for task in ready_tasks:
        #     if not isinstance(task.task_spec, UserTask):
        #         wf.complete_task_from_id(task.id)

        tasks = [t for t in ready_tasks if t.task_spec.name == task_name]
        if not tasks or len(tasks) > 1 and not isinstance(tasks[0].task_spec, UserTask):
            return

        task = tasks[0]
        self._print_task_data(wf)

        task.update_data(data)
        wf.complete_task_from_id(task.id)
        wf.do_engine_steps()
        ready_tasks = wf.get_ready_user_tasks()

        self.save_workflow_state(wf)

        task_instance = Task.objects.get(workflow=self, task_name_id=task_name)
        task_instance.complete()

        self.create_user_tasks(
            [task for task in ready_tasks if isinstance(task.task_spec, UserTask)]
        )

    def save_workflow_state(self, wf):
        state = self.get_serializer().serialize_workflow(wf)
        self.serialized_workflow_state = state
        self.save()

    def get_or_restore_workflow_state(self, do_engine_steps=True):

        if self.serialized_workflow_state:
            print("RESTORE WORKFLOW")
            wf = self.get_serializer().deserialize_workflow(
                self.serialized_workflow_state, workflow_spec=None
            )
            wf = self.get_script_engine(wf)
            return wf
        else:
            print("INIT WORKFLOW")
            wf = BpmnWorkflow(self.get_workflow_spec())
            self.save_workflow_state(wf)
            return self.get_or_restore_workflow_state()

    def set_initial_data(self, data):
        wf = self.get_or_restore_workflow_state()

        first_task = wf.get_tasks(SpiffWorkflowTask.READY)[0]

        # TODO: how to set initial data
        wf.set_data(**data)
        first_task.update_data(data)
        first_task.task_spec.set_data(**data)

        self._print_task_data(wf)

        wf.do_engine_steps()
        ready_tasks = wf.get_ready_user_tasks()

        self.save_workflow_state(wf)
        self.create_user_tasks(ready_tasks)
        return wf

    def __str__(self):
        return f"{self.id}, case: {self.case.id}"


class Task(models.Model):
    completed = models.BooleanField(
        default=False,
    )
    name = models.CharField(
        max_length=255,
    )
    task_name_id = models.CharField(
        max_length=255,
    )
    roles = ArrayField(
        base_field=models.CharField(max_length=255),
        default=list,
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    case = models.ForeignKey(
        to=Case,
        related_name="tasks",
        on_delete=models.CASCADE,
    )
    workflow = models.ForeignKey(
        to=Workflow,
        related_name="tasks",
        on_delete=models.CASCADE,
    )

    def complete(self):
        self.completed = True
        self.save()

    class Meta:
        unique_together = [["task_name_id", "workflow"]]
