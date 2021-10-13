import copy
import datetime
import logging
from string import Template

from apps.cases.models import Case
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_duration
from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.task import Task
from utils.managers import BulkCreateSignalsManager

from .utils import (
    compare_workflow_specs_by_task_specs,
    get_workflow_path,
    get_workflow_spec,
    parse_task_spec_form,
    workflow_health_check,
)

logger = logging.getLogger(__name__)


class CaseWorkflow(models.Model):
    WORKFLOW_TYPE_MAIN = "main_workflow"
    WORKFLOW_TYPE_SUB = "sub_workflow"
    WORKFLOW_TYPE_DIRECTOR = "director"
    WORKFLOW_TYPE_VISIT = "visit"
    WORKFLOW_TYPE_SUMMON = "summon"
    WORKFLOW_TYPE_DECISION = "decision"
    WORKFLOW_TYPE_RENOUNCE_DECISION = "renounce_decision"
    WORKFLOW_TYPE_CLOSE_CASE = "close_case"
    WORKFLOW_TYPES = (
        (WORKFLOW_TYPE_MAIN, WORKFLOW_TYPE_MAIN),
        (WORKFLOW_TYPE_SUB, WORKFLOW_TYPE_SUB),
        (WORKFLOW_TYPE_DIRECTOR, WORKFLOW_TYPE_DIRECTOR),
        (WORKFLOW_TYPE_VISIT, WORKFLOW_TYPE_VISIT),
        (WORKFLOW_TYPE_SUMMON, WORKFLOW_TYPE_SUMMON),
        (WORKFLOW_TYPE_DECISION, WORKFLOW_TYPE_DECISION),
        (WORKFLOW_TYPE_RENOUNCE_DECISION, WORKFLOW_TYPE_RENOUNCE_DECISION),
        (WORKFLOW_TYPE_CLOSE_CASE, WORKFLOW_TYPE_CLOSE_CASE),
    )

    case = models.ForeignKey(
        to=Case,
        related_name="workflows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    parent_workflow = models.ForeignKey(
        to="workflow.CaseWorkflow",
        related_name="child_workflows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
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
    )
    workflow_theme_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    serialized_workflow_state = models.JSONField(null=True)
    data = models.JSONField(null=True)

    completed = models.BooleanField(
        default=False,
    )

    serializer = BpmnSerializer

    def get_serializer(self):
        return self.serializer()

    def get_workflow_spec(self):
        path = get_workflow_path(
            self.workflow_type,
            self.workflow_theme_name,
            self.workflow_version,
        )
        spec = get_workflow_spec(path, self.workflow_type)
        return spec

    def get_script_engine(self, wf):
        # injects functions in workflow
        case = self.case
        workflow_instance = self

        def set_status(input):
            case.set_state(input, workflow_instance)

        def wait_for_workflows_and_send_message(message):
            logger.info(f"wait_for_workflows_and_send_message: {message}")
            logger.info(f"workflow id: {workflow_instance.id}")

            # tell the other workfows that this one is waiting
            workflow_instance.data.update(
                {
                    message: "done",
                }
            )
            workflow_instance.save(update_fields=["data"])
            all_workflows = CaseWorkflow.objects.filter(case=workflow_instance.case)

            workflows_completed = [
                a
                for a in all_workflows.values_list("data", flat=True)
                if a.get(message, "done")
            ]
            main_workflow = all_workflows.filter(main_workflow=True).first()

            """
            Tests if all workflows reached thit point,
            so the last waiting worklfow kan tell the main workflow to accept the message after all, so only the main workflow can resume
            """
            if len(workflows_completed) == all_workflows.count() and main_workflow:
                from .tasks import accept_message_for_workflow

                # pick up all summons and pass them on to the main workflow
                all_summons = [
                    d.get("summon_id")
                    for d in all_workflows.values_list("data", flat=True)
                    if d.get("summon_id")
                ]
                extra_data = {
                    "all_summons": all_summons,
                }

                # sends the accept message to a task, because we have to wait until this current tasks, we are in, is completed
                accept_message_for_workflow.delay(main_workflow.id, message, extra_data)

                # TODO: cleanup(delete others), but the message is not send yet, so below should wait
                # other_workflows = all_workflows.exclude(id=main_workflow.id)
                # other_workflows.delete()

        def start_subworkflow(subworkflow_name):
            from .tasks import task_start_subworkflow

            task_start_subworkflow.delay(subworkflow_name, workflow_instance.id)

        def parse_duration_string(str_duration):
            return parse_duration(str_duration)

        wf.script_engine = BpmnScriptEngine(
            scriptingAdditions={
                "set_status": set_status,
                "wait_for_workflows_and_send_message": wait_for_workflows_and_send_message,
                "start_subworkflow": start_subworkflow,
                "parse_duration": parse_duration_string,
            }
        )
        return wf

    def message(self, message_name, payload, resultVar, extra_data={}):
        # use this to start a workflow at a certain point
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return

        wf = self._initial_data(wf, extra_data)
        wf = self._update_workflow(wf)

        wf.message(message_name, payload, resultVar)

        wf = self._update_workflow(wf)
        self.save_workflow_state(wf)
        self._update_db(wf)

    def accept_message(self, message_name, extra_data):
        """
        Sends a message to a running workflow.
        If the state of task (ItermediateCatchEvent) that holds this message is 'message_name',
        than this task will be completed, and the workflow can resume.
        """

        wf = self.get_or_restore_workflow_state()
        if not wf:
            return

        wf = self._update_workflow(wf)

        if wf.last_task:
            wf.last_task.update_data(extra_data)

        wf = self._update_workflow(wf)

        wf.accept_message(message_name)

        wf = self._update_workflow(wf)
        self.save_workflow_state(wf)
        self._update_db(wf)

    def get_data(self):
        """
        TODO: data is also saved on this instance after a UserTask completed, but in between UserTasks data could diver.
        Find one solution to get current data from workflow and from the saved 'data' from this instance
        """
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return {}

        if wf.last_task:
            return wf.last_task.data
        return {}

    def set_absolete_tasks_to_completed(self, wf):
        # some tasks are absolete after wf.do_engine_steps or wf.refresh_waiting_tasks
        ready_tasks_ids = [t.id for t in wf.get_tasks(Task.READY)]

        # cleanup: sets dj tasks to completed
        task_instances = self.tasks.all().exclude(
            task_id__in=ready_tasks_ids,
        )
        updated = task_instances.update(completed=True)

        return updated

    def create_user_tasks(self, wf):
        ready_tasks = wf.get_ready_user_tasks()
        task_data = [
            CaseUserTask(
                task_id=task.id,
                task_name=task.task_spec.name,
                name=Template(task.task_spec.description).safe_substitute(task.data),
                roles=[r.strip() for r in task.task_spec.lane.split(",")],
                form=parse_task_spec_form(task.task_spec.form),
                case=self.case,
                workflow=self,
            )
            for task in ready_tasks
            if not CaseUserTask.objects.filter(
                task_id=task.id,
                task_name=task.task_spec.name,
                workflow=self,
            )
        ]
        task_instances = CaseUserTask.objects.bulk_create(task_data)

        return task_instances

    @staticmethod
    def get_task_by_task_id(id):
        task = get_object_or_404(CaseUserTask, id=id)
        return task

    @staticmethod
    def complete_user_task(id, data):
        task = CaseUserTask.objects.filter(id=id).first()
        if task:
            task.workflow.complete_user_task_and_create_new_user_tasks(
                task.task_id, data
            )

    def check_for_issues(self):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return "restore error"
        try:
            wf = self._update_workflow(wf)
        except Exception:
            return "update error"
        return "no issues"

    def complete_user_task_and_create_new_user_tasks(self, task_id=None, data=None):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return

        task = wf.get_task(task_id)

        if task and isinstance(task.task_spec, UserTask):
            task.update_data(data)
            wf.complete_task_from_id(task.id)
            logger.info(f"COMPLETE TASK: {task.task_spec.name}")
        else:
            logger.info(f"COMPLETE TASK NOT FOUND: {task_id}")

        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        self._update_db(wf)
        self._check_completed_workflows(wf)

    def save_workflow_state(self, wf):
        if wf.last_task:
            # update this workflow with the latest task data
            self.data.update(wf.last_task.data)

        state = self.get_serializer().serialize_workflow(wf, include_spec=False)
        self.serialized_workflow_state = state

        self.save()

    def get_or_restore_workflow_state(self):
        # gets the unserialized workflow from this workflow instance, it has to use an workflow_spec, witch in this case will be load from filesystem.

        try:
            workflow_spec = self.get_workflow_spec()
        except Exception as e:
            logger.error(
                f"get_workflow_spec: {self.id}, case id: {self.case.id}, error: {str(e)}"
            )
            return

        if self.serialized_workflow_state:
            try:
                wf = self.get_serializer().deserialize_workflow(
                    self.serialized_workflow_state, workflow_spec=workflow_spec
                )
                wf = self.get_script_engine(wf)
            except Exception as e:
                logger.error(
                    f"get_or_restore_workflow_state: {self.id}, case id: {self.case.id}, error: {str(e)}"
                )
                return
            return wf
        else:
            wf = BpmnWorkflow(workflow_spec)

            # always work with an already saved version
            self.save_workflow_state(wf)
            return self.get_or_restore_workflow_state()

    def _initial_data(self, wf, data):

        first_task = wf.get_tasks(Task.READY)
        last_task = wf.last_task
        if first_task:
            first_task = first_task[0]
        elif last_task:
            first_task = last_task

        # TODO: how to set initial data
        first_task.update_data(data)

        return wf

    def set_initial_data(self, data):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return

        wf = self._initial_data(wf, data)

        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        self._update_db(wf)
        return wf

    def update_workflow(self):
        # call this on a regular bases to complete tasks that are time related
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return
        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self.save_workflow_state(wf)
        self._update_db(wf)

        self._check_completed_workflows(wf)

    def _check_completed_workflows(self, wf):
        # if end of subworkflow, try to get back to main workflow
        if self.parent_workflow and wf.is_completed():

            self.parent_workflow.accept_message(
                f"resume_after_{self.workflow_type}",
                self.get_data(),
            )
            self.completed = True
            self.save()
            # maybe delete workflow object when completed
            # self.delete()

    def _update_workflow(self, wf):
        wf.refresh_waiting_tasks()
        wf.do_engine_steps()
        return wf

    def _update_db(self, wf):
        self.set_absolete_tasks_to_completed(wf)
        self.create_user_tasks(wf)

    def migrate_to(self, workflow_version, test=True):
        # tests and tries to migrate to an other version
        """
        Tests and tries to migrate to an other version
        Below the steps to perform

        *   This performs checks on the current uncompleted db tasks based on the new workflow_spec
            Check if task.task_name exists in the new workflow_spec, if not, could it be renamed.
            If it exists, is the path for the new workflow_spec to this task the same as the old one.
            At the end of the task name checks, a new task name set(maybe the same as the old one), can be used to do the next check.

        *   Perform checks on all the data gathered until this state of the workflow.
            Assemble the form fields of the spiff UserTasks on the path to current uncompleted db tasks for current and new workflow_spec.
            Compare the keys of the two results, and provide defaults for the missing data, for new fields in the new workflow_spec.

        *   Perform a fast-forward on a new workflow, based on the new workflow_spec, by completing all the UserTasks until the current uncompleted db tasks.
            This fast-forward on a workflow, could generate a exception, if a ScriptTasks uses variables that are not generated by forms.
            The result of the fast-forward, should be a new workflow based on the new workflow_spec, that can be serialized and saved in this workflow instances field 'serialized_workflow_state'
            The current uncompleted db tasks field 'task_id', should be changed to the task.id's from new workflow's Task.READY tasks.
        """

        valid = True
        path = get_workflow_path(
            self.workflow_type,
            self.workflow_theme_name,
            workflow_version,
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
            last_completed_users_task = last_completed_users_task.task_name

        valid, new_task_name_ids = compare_workflow_specs_by_task_specs(
            workflow_spec_a,
            workflow_spec_b,
            uncompleted_users_tasks.values_list("task_name", flat=True),
        )

        # translate task_name's
        expected_user_task_names = [
            new_task_name_ids.get(t.task_name, t.task_name)
            for t in uncompleted_users_tasks
        ]

        # fast forward workflow to uncompleted user task names with existing data
        result = workflow_health_check(
            workflow_spec_b, copy.deepcopy(self.data), expected_user_task_names
        )
        logger.info(result)
        if not test and valid:
            # existing uncompleted tasks can be deleted. They should be created with the new workflow with new task id's
            uncompleted_users_tasks.delete()

            self.serialized_workflow_state = ""

    def __str__(self):
        return f"{self.id}, case: {self.case.id}"

    class Meta:
        ordering = ["-id"]


USER_TASKS = {
    "task_prepare_abbreviated_visit_rapport": {
        "due_date": datetime.timedelta(days=2),
    },
    "task_create_picture_rapport": {
        "due_date": datetime.timedelta(days=2),
    },
    "task_create_report_of_findings": {
        "due_date": datetime.timedelta(days=2),
    },
}
DEFAULT_USER_TASK_DUE_DATE = datetime.timedelta(days=0)


class CaseUserTask(models.Model):

    completed = models.BooleanField(
        default=False,
    )
    # connects spiff task with this db task
    task_id = models.UUIDField(
        unique=True,
    )
    # name of the task_spec in spiff, in bpmn modeler is this the id field
    task_name = models.CharField(
        max_length=255,
    )
    # description of the task_spec in spiff, in bpmn modeler is this the name field
    name = models.CharField(
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
    due_date = models.DateTimeField(
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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
        to=CaseWorkflow,
        related_name="tasks",
        on_delete=models.CASCADE,
    )

    objects = BulkCreateSignalsManager()

    @staticmethod
    def parse_task_spec_form(form):
        # transforms and serializes the spiff task_spec.form for the current react frontend
        # TODO: only serialize task_spec.formm, and refactor react frontend
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
        # transforms form result data and adds labels for the frontend
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

    @property
    def get_form_variables(self):
        # TODO: Return corresponding spiff task data, currently used only to provide frontend with the current summon_id
        return self.workflow.get_data()

    def complete(self):
        self.completed = True
        self.save()
