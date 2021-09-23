import copy
from string import Template

from apps.cases.models import Case
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.shortcuts import get_object_or_404
from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import (
    BpmnSerializer,  # as SpiffBpmnSerializer
)
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # as SpiffBpmnWorkflow
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.task import Task as SpiffWorkflowTask

from .utils import (
    check_task_id_changes,
    compare_path_until_task,
    compare_workflow_specs_by_task_specs,
    get_workflow_path,
    get_workflow_spec,
    parse_task_spec_form,
    workflow_health_check,
)


def get_workflow_spec_choices():
    return [[k, k] for k, v in settings.WORKFLOWS.items()]


def get_workflow_version_choices():
    return [[v, v] for v in settings.WORKFLOW_VERSIONS]


class Workflow(models.Model):
    WORKFLOW_TYPE_MAIN = "main_workflow"
    WORKFLOW_TYPE_SUB = "sub_workflow"
    WORKFLOW_TYPES = (
        (WORKFLOW_TYPE_MAIN, WORKFLOW_TYPE_MAIN),
        (WORKFLOW_TYPE_SUB, WORKFLOW_TYPE_SUB),
    )

    case = models.ForeignKey(
        to=Case,
        related_name="workflows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    # workflow_spec = models.CharField(
    #     max_length=100,
    #     choices=get_workflow_spec_choices(),
    #     default=get_workflow_spec_choices()[0][0],
    # )
    main_workflow = models.BooleanField(
        default=False,
    )
    workflow_type = models.CharField(
        max_length=100,
        choices=WORKFLOW_TYPES,
        default=WORKFLOW_TYPES[0][0],
    )
    workflow_version = models.CharField(
        max_length=100,
        choices=get_workflow_version_choices(),
        default=get_workflow_version_choices()[0][0],
    )
    created = models.DateTimeField(auto_now_add=True)
    # initial_message = models.CharField(
    #     max_length=100,
    #     null=True,
    #     blank=True,
    # )
    serialized_workflow_state = models.JSONField(null=True)
    data = models.JSONField(null=True)

    serializer = BpmnSerializer

    def save(self, *args, **kwargs):
        self.data = self.data if isinstance(self.data, dict) else {}
        return super().save(*args, **kwargs)

    def _get_strip_extensie(self, file_name):
        return file_name.split(".")[0]

    def get_serializer(self):
        return self.serializer()

    def get_workflow_spec(self):
        path = get_workflow_path(
            self.case.theme.name,
            self.workflow_version,
            self.workflow_type,
        )
        spec = get_workflow_spec(path, self.workflow_type)
        # print("Duplicate task spec ids: %s" % check_for_duplicate_task_spec_ids(spec))
        return spec

    def first_task(self):
        wf = self.get_or_restore_workflow_state()
        tasks = wf.get_tasks()
        return tasks[0]

    def get_script_engine(self, wf):
        # injects functions in workflow
        case = self.case
        workflow_instance = self

        def set_status(input):
            print("set_status: %s" % input)
            case.set_state(input, workflow_instance)

        def wait_for_workflows_and_send_message(message):
            print("wait_for_workflows_and_send_message: %s" % message)
            print("workflow id: %s" % workflow_instance.id)

            workflow_instance.data.update(
                {
                    message: "done",
                }
            )
            workflow_instance.save(update_fields=["data"])
            all_workflows = Workflow.objects.filter(case=workflow_instance.case)

            workflows_completed = [
                a
                for a in all_workflows.values_list("data", flat=True)
                if a.get(message, "done")
            ]
            main_workflow = all_workflows.filter(main_workflow=True).first()

            # tests if all workflows reached thit point
            if len(workflows_completed) == all_workflows.count() and main_workflow:

                # pick up all summons and pass them on to the main workflow
                all_summons = [
                    d.get("summon_id")
                    for d in all_workflows.values_list("data", flat=True)
                    if d.get("summon_id")
                ]
                messages = main_workflow.data.get("messages", [])

                # add message to main workflow, this will tell only the main workflow to go on
                messages.append(message)
                main_workflow.data.update(
                    {
                        "messages": messages,
                        "all_summons": all_summons,
                    }
                )
                main_workflow.save(update_fields=["data"])
                main_workflow.update_workflow()

                # delete others
                other_workflows = all_workflows.exclude(id=main_workflow.id)
                other_workflows.delete()

        wf.script_engine = BpmnScriptEngine(
            scriptingAdditions={
                "set_status": set_status,
                "wait_for_workflows_and_send_message": wait_for_workflows_and_send_message,
            }
        )
        return wf

    def _print_task_data(self, wf):
        print("START: print data")
        print(wf.name)
        wf.dump()
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
            return Task.parse_task_spec_form(task.task_spec.form)
        return []

    def message(self, message_name, payload, resultVar, extra_data={}):
        wf = self.get_or_restore_workflow_state()

        wf = self._update_workflow(wf)
        wf = self._message(wf, message_name, payload, resultVar, extra_data)

        wf = self._update_workflow(wf)
        self.save_workflow_state(wf)
        self._update_db(wf)

    def accept_message(self, message_name):
        wf = self.get_or_restore_workflow_state()

        wf.accept_message(message_name)

        wf = self._update_workflow(wf)
        self.save_workflow_state(wf)
        self._update_db(wf)

    @staticmethod
    def _message(wf, message_name, payload, resultVar, extra_data={}):

        wf.message(message_name, payload, resultVar)
        first_task = wf.get_tasks(SpiffWorkflowTask.READY)
        if first_task and extra_data and isinstance(extra_data, dict):
            first_task[0].update_data(extra_data)
        return wf

    def get_data(self):
        wf = self.get_or_restore_workflow_state()
        return wf.last_task.data

    def set_absolete_tasks_to_completed(self, wf):
        # some tasks are absolete after wf.do_engine_steps or wf.refresh_waiting_tasks
        ready_tasks_ids = [t.id for t in wf.get_tasks(SpiffWorkflowTask.READY)]

        # cleanup: sets dj tasks to completed
        task_instances = self.tasks.all().exclude(
            task_id__in=ready_tasks_ids,
        )
        updated = task_instances.update(completed=True)

        return updated

    def create_user_tasks(self, wf):
        ready_tasks = wf.get_ready_user_tasks()
        task_data = [
            Task(
                task_id=task.id,
                task_name_id=task.task_spec.name,
                name=Template(task.task_spec.description).safe_substitute(task.data),
                roles=[r.strip() for r in task.task_spec.lane.split(",")],
                form=parse_task_spec_form(task.task_spec.form),
                case=self.case,
                workflow=self,
            )
            for task in ready_tasks
            if not Task.objects.filter(
                task_id=task.id,
                task_name_id=task.task_spec.name,
                workflow=self,
            )
        ]
        task_instances = Task.objects.bulk_create(task_data)

        return task_instances

    @staticmethod
    def get_spec_names_by_process_id():
        return dict((v.get("main_proccess"), k) for k, v in settings.WORKFLOWS.items())

    @staticmethod
    def get_task_by_task_id(id):
        task = get_object_or_404(Task, id=id)
        return task

    @staticmethod
    def complete_user_task(id, data):
        task = Task.objects.get(id=id)
        task.workflow.complete_user_task_and_create_new_user_tasks(task.task_id, data)

    def complete_user_task_and_create_new_user_tasks(self, task_id=None, data=None):
        wf = self.get_or_restore_workflow_state()

        task = wf.get_task(task_id)

        if task and isinstance(task.task_spec, UserTask):
            task.update_data(data)
            wf.complete_task_from_id(task.id)
            print("COMPLETE TASK: %s" % task.task_spec.name)
        else:
            print("COMPLETE TASK NOT FOUND: %s" % task_id)

        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        self._update_db(wf)

    def fast_forward(self, wf):
        test_result = workflow_health_check(
            wf.last_task.data, [t.task_spec.name for t in wf.get_ready_user_tasks()]
        )
        print(test_result)

    def save_workflow_state(self, wf):
        if wf.last_task:
            # update this workflow with the latest task data
            self.data.update(wf.last_task.data)

        state = self.get_serializer().serialize_workflow(wf, include_spec=False)
        self.serialized_workflow_state = state

        self.save()

    def get_or_restore_workflow_state(self):
        if self.serialized_workflow_state:
            wf = self.get_serializer().deserialize_workflow(
                self.serialized_workflow_state, workflow_spec=self.get_workflow_spec()
            )
            wf = self.get_script_engine(wf)
            return wf
        else:
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
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        self._update_db(wf)
        return wf

    def update_workflow(self):
        # call this on a regular bases to complete tasks that are time related
        wf = self.get_or_restore_workflow_state()

        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        self._update_db(wf)

    def _update_workflow(self, wf):
        for message in self.data.get("messages", []):
            wf.accept_message(message)
        wf.refresh_waiting_tasks()
        wf.do_engine_steps()
        return wf

    def _update_db(self, wf):
        self.set_absolete_tasks_to_completed(wf)
        self.create_user_tasks(wf)

    def migrate_to(self, workflow_version, test=True):
        valid = True
        path = get_workflow_path(
            self.case.theme.name,
            workflow_version,
            self.workflow_type,
        )
        try:
            workflow_spec_b = get_workflow_spec(path, self.workflow_type)
        except Exception:
            return f"Version '{workflow_version}' not found"

        workflow_spec_a = self.get_workflow_spec()

        uncompleted_users_tasks = self.tasks.filter(completed=False)
        last_completed_users_task = (
            self.tasks.filter(completed=True).order_by("updated").first()
        )
        if last_completed_users_task:
            last_completed_users_task = last_completed_users_task.task_name_id

        valid, new_task_name_ids = compare_workflow_specs_by_task_specs(
            workflow_spec_a,
            workflow_spec_b,
            uncompleted_users_tasks.values_list("task_name_id", flat=True),
        )

        # translate task_name_id's
        expected_user_task_names = [
            new_task_name_ids.get(t.task_name_id, t.task_name_id)
            for t in uncompleted_users_tasks
        ]

        # fast forward workflow to uncompleted user task names with existing data
        result = workflow_health_check(
            workflow_spec_b, copy.deepcopy(self.data), expected_user_task_names
        )
        print(result)
        if not test and valid:
            # existing uncompleted tasks can be deleted. They should be created with the new workflow with new task id's
            uncompleted_users_tasks.delete()

            self.serialized_workflow_state = ""

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
    updated = models.DateTimeField(auto_now=True)
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

    @staticmethod
    def parse_task_spec_form(form):
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
                "required": bool(
                    [
                        v.__dict__
                        for v in f.__dict__.get("validation", [])
                        if v.__dict__.get("name") == "required"
                    ]
                ),
            }
            for f in form.fields
        ]
        return fields

    def map_variables_on_form(self, variables):
        form = dict((f.get("id"), f) for f in self.form)
        return dict(
            (
                k,
                {
                    "label": form.get(k, {}).get("label", v.get("value")),
                    "value": v.get("value")
                    if not form.get(k, {}).get("options")
                    else dict((o.get("id"), o) for o in form.get(k, {}).get("options"))
                    .get(v.get("value"), {})
                    .get("label", v.get("value")),
                },
            )
            for k, v in variables.items()
            if isinstance(v, dict)
        )

    def get_form_variables(self):
        return {}

    def complete(self):
        self.completed = True
        self.save()
