import copy
import logging
from string import Template

from apps.cases.models import Case, CaseTheme
from apps.events.models import CaseEvent, TaskModelEventEmitter
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_duration
from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.specs.event_definitions import TimerEventDefinition
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.task import Task
from utils.managers import BulkCreateSignalsManager

from .tasks import (
    redis_lock,
    release_lock,
    task_complete_user_task_and_create_new_user_tasks,
    task_complete_worflow,
    task_start_subworkflow,
    task_wait_for_workflows_and_send_message,
)
from .utils import (
    compare_workflow_specs_by_task_specs,
    get_initial_data_from_config,
    get_workflow_path,
    get_workflow_spec,
    parse_task_spec_form,
    workflow_health_check,
)

logger = logging.getLogger(__name__)


class CaseWorkflow(models.Model):
    WORKFLOW_TYPE_MAIN = "main_workflow"
    WORKFLOW_TYPE_SUB = "sub_workflow"
    WORKFLOW_TYPE_CLOSING_PROCEDURE = "closing_procedure"
    WORKFLOW_TYPE_DEBRIEF = "debrief"
    WORKFLOW_TYPE_DIRECTOR = "director"
    WORKFLOW_TYPE_VISIT = "visit"
    WORKFLOW_TYPE_SUMMON = "summon"
    WORKFLOW_TYPE_DECISION = "decision"
    WORKFLOW_TYPE_RENOUNCE_DECISION = "renounce_decision"
    WORKFLOW_TYPE_CLOSE_CASE = "close_case"
    WORKFLOW_TYPES = (
        (WORKFLOW_TYPE_MAIN, WORKFLOW_TYPE_MAIN),
        (WORKFLOW_TYPE_SUB, WORKFLOW_TYPE_SUB),
        (WORKFLOW_TYPE_DEBRIEF, WORKFLOW_TYPE_DEBRIEF),
        (WORKFLOW_TYPE_CLOSING_PROCEDURE, WORKFLOW_TYPE_CLOSING_PROCEDURE),
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
        default=WORKFLOW_TYPE_DIRECTOR,
    )
    workflow_version = models.CharField(
        max_length=100,
    )
    workflow_theme_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    workflow_message_name = models.CharField(
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

    def get_lock_id(self):
        return f"caseworkflow-lock-{self.id}"

    def get_lock(self):
        return redis_lock(self.get_lock_id())

    def release_lock(self):
        release_lock(self.get_lock_id())

    def get_serializer(self):
        return self.serializer()

    def get_workflow_spec(self):
        try:
            path = get_workflow_path(
                self.workflow_type,
                self.workflow_theme_name,
                self.workflow_version,
            )
            spec = get_workflow_spec(path, self.workflow_type)
        except Exception as e:
            logger.error(
                f"get_workflow_spec: {self.id}, case id: {self.case.id}, error: {str(e)}"
            )
            return

        return spec

    def get_script_engine(self, wf):
        # injects functions in workflow
        case = self.case
        workflow_instance = self

        def set_status(input):
            case.set_state(input, workflow_instance)

        def wait_for_workflows_and_send_message(message):
            task_wait_for_workflows_and_send_message.delay(
                workflow_instance.id, message
            )

        def start_subworkflow(subworkflow_name):
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

    # legacy method, should be removed if all directors use version >=1.0.0
    def handle_message_catch_event_next_step(self, workflow_instance):
        return self.handle_message_wait_for_summons(workflow_instance)

    def handle_message_wait_for_summons(self, workflow_instance):
        from apps.decisions.models import Decision

        message = "message_wait_for_summons"

        # tell the other workfows that this one is waiting
        workflow_instance.data.update(
            {
                message: "done",
            }
        )
        workflow_instance.save(update_fields=["data"])
        all_workflows = CaseWorkflow.objects.filter(
            case=workflow_instance.case,
            workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
        )

        workflows_completed = [
            a
            for a in all_workflows.values_list("data", flat=True)
            if a.get(message) == "done"
        ]

        main_workflow = all_workflows.filter(main_workflow=True).first()
        """
        Tests if all workflows reached thit point,
        so the last waiting worklfow kan tell the main workflow to accept the message after all, so only the main workflow can resume
        """
        if len(workflows_completed) == all_workflows.count() and main_workflow:

            # pick up all summons and pass them on to the main workflow
            all_summons = [
                d.get("summon_id")
                for d in all_workflows.values_list("data", flat=True)
                if d.get("summon_id")
            ]
            extra_data = {
                "next_step": {"value": "default"},
                "all_summons": all_summons,
                "decision_count": {
                    "value": Decision.objects.filter(case=main_workflow.case)
                    .exclude(decision_type__workflow_option="no_decision")
                    .count()
                },
            }

            next_step_visit = [
                cwf
                for cwf in all_workflows
                if cwf.get_data().get("summon_next_step", {}).get("value") == "visit"
            ]
            if next_step_visit:
                extra_data.update(
                    {
                        "next_step": {"value": "visit"},
                    }
                )

            other_workflows = all_workflows.exclude(id=main_workflow.id)

            for workflow in other_workflows:
                workflow.complete_workflow()

            return extra_data
        return False

    def start(self, data={}):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return

        initial_data = get_initial_data_from_config(
            self.workflow_theme_name,
            self.workflow_type,
            self.workflow_version,
            self.workflow_message_name,
        )

        if isinstance(data, dict):
            initial_data.update(data)
        initial_data.update(self.data)

        wf = self._initial_data(wf, initial_data)

        wf = self._update_workflow(wf)

        if self.workflow_message_name:
            wf.message(
                self.workflow_message_name, self.workflow_message_name, "message_name"
            )
            wf = self._update_workflow(wf)

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

    def complete_workflow(self):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return
        wf.complete_all(False, False)
        # TODO: There are probably still waiting tasks active, so cleanup, if we should not wait for those tasks

        self.completed = True

        self._update_db(wf)

    def update_tasks(self, wf):
        self.set_absolete_tasks_to_completed(wf)
        self.create_user_tasks(wf)

    @staticmethod
    def get_task_by_task_id(id):
        task = get_object_or_404(CaseUserTask, id=id)
        return task

    @staticmethod
    def complete_user_task(id, data):
        task_complete_user_task_and_create_new_user_tasks.delay(id, data)

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
            logger.info(
                f"COMPLETE TASK: {task.task_spec.name}, case: {self.case.id}-{self.workflow_type}"
            )
        else:
            logger.info(f"COMPLETE TASK NOT FOUND: {task_id}")

        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self._update_db(wf)

    def save_workflow_state(self, wf):
        if wf.last_task:
            # update this workflow with the latest task data
            self.data.update(wf.last_task.data)

        completed = False

        if wf.is_completed() and not self.completed:
            completed = True
            self.completed = True

        state = self.get_serializer().serialize_workflow(wf, include_spec=False)
        self.serialized_workflow_state = state

        self.save()

        if completed:
            data = copy.deepcopy(wf.last_task.data) if wf.last_task else {}
            task_complete_worflow.delay(self.id, data)

    def get_or_restore_workflow_state(self):
        # gets the unserialized workflow from this workflow instance, it has to use an workflow_spec, witch in this case will be load from filesystem.
        workflow_spec = self.get_workflow_spec()
        if not workflow_spec:
            return

        if self.serialized_workflow_state:
            try:
                wf = self.get_serializer().deserialize_workflow(
                    self.serialized_workflow_state, workflow_spec=workflow_spec
                )
                wf = self.get_script_engine(wf)
            except Exception:
                return False
            return wf
        else:
            wf = BpmnWorkflow(workflow_spec)
            wf = self.get_script_engine(wf)
            return wf

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

    def update_workflow(self):
        # call this on a regular bases to complete tasks that are time related
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return
        # changes the workflow
        wf = self._update_workflow(wf)

        # no changes to the workflow after this point
        self._update_db(wf)

    def has_a_timer_event_fired(self):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return False
        waiting_tasks = wf._get_waiting_tasks()
        for task in waiting_tasks:
            if hasattr(task.task_spec, "event_definition") and isinstance(
                task.task_spec.event_definition, TimerEventDefinition
            ):
                event_definition = task.task_spec.event_definition
                has_fired = event_definition.has_fired(task)
                if has_fired:
                    logger.info(
                        f"TimerEventDefinition for task '{task.task_spec.name}' has expired. Workflow with id '{self.id}', needs an update"
                    )
                    return True
        return False

    def _update_workflow(self, wf):
        wf.refresh_waiting_tasks()
        wf.do_engine_steps()
        return wf

    def _update_db(self, wf):
        with transaction.atomic():
            self.save_workflow_state(wf)
            self.update_tasks(wf)
            transaction.on_commit(lambda: self.release_lock())

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
    due_date = models.DateTimeField()
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

    @property
    def get_form_variables(self):
        # TODO: Return corresponding spiff task data, currently used only to provide frontend with the current summon_id
        return self.workflow.get_data()

    def complete(self):
        self.completed = True
        self.save()


class WorkflowOption(models.Model):
    name = models.CharField(max_length=255)
    message_name = models.CharField(max_length=255)
    to_directing_proccess = models.BooleanField(default=False)
    theme = models.ForeignKey(
        to=CaseTheme,
        related_name="workflow_options",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.name} - {self.message_name}"

    class Meta:
        ordering = ["name"]


class GenericCompletedTask(TaskModelEventEmitter):
    EVENT_TYPE = CaseEvent.TYPE_GENERIC_TASK

    case = models.ForeignKey(
        to=Case,
        related_name="generic_completed_tasks",
        on_delete=models.CASCADE,
    )
    date_added = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="generic_completed_tasks",
        on_delete=models.PROTECT,
    )
    variables = models.JSONField(null=True)

    def __get_event_values__(self):
        variables = self.variables.get("mapped_form_data", {}) or self.variables
        return {
            "author": self.author.__str__(),
            "date_added": self.date_added,
            "description": self.description,
            "variables": variables,
        }
