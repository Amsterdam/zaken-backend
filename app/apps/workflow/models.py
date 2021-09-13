from string import Template

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
        default=get_workflow_spec_choices()[0][0],
    )
    serialized_workflow_state = models.JSONField(null=True)
    data = models.JSONField(null=True)

    serializer = BpmnSerializer
    proccess_conf = settings.DEFAULT_WORKFLOW

    def _get_strip_extensie(self, file_name):
        return file_name.split(".")[0]

    def _task_form_to_python(self, form):
        trans_types = {
            "enum": "select",
            "boolean": "checkbox",
        }
        fields = [
            {
                **f.__dict__,
                "options": [
                    {
                        **o.__dict__,
                        "value": o.__dict__.get("id"),
                        "label": o.__dict__.get("name"),
                    }
                    for o in f.__dict__.get("options", [])
                ],
                "name": f.__dict__.get("id"),
                "validation": [v.__dict__ for v in f.__dict__.get("validation", [])],
                "type": trans_types.get(f.__dict__.get("type"), "text"),
            }
            for f in form.fields
        ]
        return fields

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

    def first_task(self):
        wf = self.get_or_restore_workflow_state()
        tasks = wf.get_tasks()

        return tasks[0]

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
        print(wf.dump())
        for t in wf.get_tasks():
            print("-")
            print(t.get_state_name())
            print(t.workflow.name)
            print(t.task_spec.name)
            print(t.last_state_change)
            print(t.state_history)
            print(t.log)
            print(t.data)
            print(t.task_info())
        print("END: print data")

    def get_user_task_form(self, task_id):
        wf = self.get_or_restore_workflow_state()
        task = wf.get_task(task_id)
        if task:
            return self._task_form_to_python(task.task_spec.form)
        return []

    def message(self, message_name, payload, resultVar):
        wf = self.get_or_restore_workflow_state()
        wf.do_engine_steps()
        wf.message(message_name, payload, resultVar)
        wf = self._update_workflow(wf)
        self.save_workflow_state(wf)

    def set_canceled_tasks_to_completed(self, wf):
        # some tasks are absolete after wf.do_engine_steps or wf.refresh_waiting_tasks
        cancelled_tasks_ids = [t.id for t in wf.get_tasks(SpiffWorkflowTask.CANCELLED)]

        # cleanup: sets dj tasks to completed if exists in spiff cancelled tasks
        task_instances = Task.objects.filter(
            task_id__in=cancelled_tasks_ids,
            workflow=self,
            completed=False,
        )
        task_instances.update(completed=True)

        return cancelled_tasks_ids

    def create_user_tasks(self, wf):
        ready_tasks = wf.get_ready_user_tasks()
        task_data = [
            Task(
                task_id=task.id,
                task_name_id=task.task_spec.name,
                name=Template(task.task_spec.description).safe_substitute(task.data),
                roles=[r.strip() for r in task.task_spec.lane.split(",")],
                form=self._task_form_to_python(task.task_spec.form),
                case=self.case,
                workflow=self,
            )
            for task in ready_tasks
            if not Task.objects.filter(
                task_id=task.id,
                task_name_id=task.task_spec.name,
                completed=False,
                workflow=self,
            )
        ]
        task_instances = Task.objects.bulk_create(task_data)

        return task_instances

    @staticmethod
    def get_spec_names_by_process_id():
        return dict((v.get("main_proccess"), k) for k, v in settings.WORKFLOWS.items())

    @staticmethod
    def complete_user_task(id, data):
        task = Task.objects.get(id=id)
        task.workflow.complete_user_task_and_create_new_user_tasks(task.task_id, data)

    def complete_user_task_and_create_new_user_tasks(self, task_id=None, data=None):
        wf = self.get_or_restore_workflow_state()

        # wf.do_engine_steps()
        task = wf.get_task(task_id)

        if task and isinstance(task.task_spec, UserTask):
            task.update_data(data)
            wf.complete_task_from_id(task.id)

        self._print_task_data(wf)
        # changes the workflow
        wf = self._update_workflow(wf)

        task_instance = Task.objects.filter(
            workflow=self,
            task_id=task_id,
            completed=False,
        ).first()
        if task_instance:
            task_instance.complete()

        # no changes to the workflow after this point
        self.save_workflow_state(wf)

    def save_workflow_state(self, wf):
        # print(wf.last_task.data)
        completed_tasks = wf.get_tasks(SpiffWorkflowTask.COMPLETED)
        if completed_tasks:
            self.data = completed_tasks[-1].data
        state = self.get_serializer().serialize_workflow(wf, include_spec=False)
        self.serialized_workflow_state = state
        print("SAVE WORKFLOW")
        self.save()

    def get_or_restore_workflow_state(self, do_engine_steps=True):

        if self.serialized_workflow_state:
            print("RESTORE WORKFLOW")
            wf = self.get_serializer().deserialize_workflow(
                self.serialized_workflow_state, workflow_spec=self.get_workflow_spec()
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

        # changes the workflow
        # wf.do_engine_steps()
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        return wf

    def update_workflow(self):
        # call this on a regular bases to complete tasks that are time related

        wf = self.get_or_restore_workflow_state()
        # print(f"START CASE ID:{self.case.id}")

        # print("all_waiting_tasks")
        # print(wf.get_tasks(SpiffWorkflowTask.WAITING))

        # changes the workflow
        wf = self._update_workflow(wf)

        # print("remaining_waiting_tasks")
        # print(wf.get_tasks(SpiffWorkflowTask.WAITING))

        # no changes to the workflow after this point
        self.save_workflow_state(wf)

        # print(f"END CASE ID:{self.case.id}")

    def _update_workflow(self, wf):
        wf.refresh_waiting_tasks()
        wf.do_engine_steps()
        self.set_canceled_tasks_to_completed(wf)
        self.create_user_tasks(wf)
        return wf

    def __str__(self):
        return f"{self.id}, case: {self.case.id}"


class Task(models.Model):
    completed = models.BooleanField(
        default=False,
    )
    task_id = models.UUIDField(
        unique=True,
    )
    name = models.CharField(
        max_length=255,
    )
    task_name_id = models.CharField(
        max_length=255,
    )
    form = models.JSONField(
        default=list,
        null=True,
        blank=True,
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

    def get_form_variables(self):
        return {}

    def complete(self):
        self.completed = True
        self.save()
