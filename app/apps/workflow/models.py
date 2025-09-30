import copy
import datetime
import logging
from string import Template

from apps.cases.models import Case, CaseStateType, CaseTheme
from apps.events.models import CaseEvent, TaskModelEventEmitter
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_duration
from packaging import version
from SpiffWorkflow import TaskState
from SpiffWorkflow.bpmn import BpmnEvent
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.specs.control import BoundaryEvent
from SpiffWorkflow.bpmn.specs.event_definitions.timer import TimerEventDefinition
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.serializer.config import CAMUNDA_CONFIG
from SpiffWorkflow.camunda.specs.event_definitions import MessageEventDefinition
from SpiffWorkflow.camunda.specs.user_task import UserTask
from utils.managers import BulkCreateSignalsManager

from .tasks import (
    redis_lock,
    release_lock,
    task_complete_user_task_and_create_new_user_tasks,
    task_complete_worflow,
    task_script_wait,
    task_start_subworkflow,
    task_update_workflow,
    task_wait_for_workflows_and_send_message,
)
from .utils import (
    ff_to_subworkflow,
    ff_workflow,
    get_initial_data_from_config,
    get_latest_version_from_config,
    get_workflow_path,
    get_workflow_spec,
    parse_task_spec_form,
    timedelta_to_iso_duration,
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
    WORKFLOW_TYPE_DIGITAL_SURVEILLANCE = "digital_surveillance"
    WORKFLOW_TYPE_HOUSING_CORPORATION = "housing_corporation"
    WORKFLOW_TYPE_UNOCCUPIED = "unoccupied"
    WORKFLOW_TYPE_CITIZEN_REPORT_FEEDBACK = "citizen_report_feedback"
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
        (WORKFLOW_TYPE_DIGITAL_SURVEILLANCE, WORKFLOW_TYPE_DIGITAL_SURVEILLANCE),
        (WORKFLOW_TYPE_HOUSING_CORPORATION, WORKFLOW_TYPE_HOUSING_CORPORATION),
        (WORKFLOW_TYPE_UNOCCUPIED, WORKFLOW_TYPE_UNOCCUPIED),
        (WORKFLOW_TYPE_CITIZEN_REPORT_FEEDBACK, WORKFLOW_TYPE_CITIZEN_REPORT_FEEDBACK),
    )

    SUBWORKFLOWS = (
        "housing_corporation",
        "digital_surveillance",
        "visit",
        "debrief",
        "summon",
        "decision",
        "renounce_decision",
        "closing_procedure",
        "close_case",
        "unoccupied",
        WORKFLOW_TYPE_CITIZEN_REPORT_FEEDBACK,
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
    date_modified = models.DateTimeField(auto_now=True)
    serialized_workflow_state = models.JSONField(null=True)
    data = models.JSONField(null=True)

    case_state_type = models.ForeignKey(
        to="cases.CaseStateType",
        related_name="workflows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    started = models.BooleanField(
        default=False,
    )
    completed = models.BooleanField(
        default=False,
    )

    serializer = BpmnWorkflowSerializer

    def ensure_data_dict(self):
        if self.data is None:
            self.data = {}

    def get_workflow_exclude_options(self):
        if self.workflow_type != CaseWorkflow.WORKFLOW_TYPE_SUMMON:
            return []

        summon_version = version.parse(self.workflow_version)

        exclude_options = []

        # Version is lower than 6.3, remove these options because they are not present in that BPMN version
        if summon_version < version.parse("6.3.0"):
            exclude_options = ["besluit", "informatiebrief", "geen_zienswijze"]
        elif summon_version < version.parse("7.2.0"):  # covers versions 6.3.0 to 7.1.0
            exclude_options = ["informatiebrief", "geen_zienswijze"]
        elif summon_version < version.parse("7.3.0"):  # covers version 7.2.0
            exclude_options = ["geen_zienswijze"]

        return exclude_options

    def get_workflow_exclude_names(self):
        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_SUMMON:
            summon_version = version.parse(self.workflow_version)
            # Version is equal or higher than 7.3.0, remove this option because it's replaced by another route in the BPMN-model.
            if summon_version >= version.parse("7.3.0"):
                exclude_names = ["Voornemen intrekking BB-vergunning"]
            else:
                exclude_names = []

            return exclude_names

    def get_lock_id(self):
        return f"caseworkflow-lock-{self.id}"

    def get_lock(self):
        return redis_lock(self.get_lock_id())

    def release_lock(self):
        release_lock(self.get_lock_id())

    def get_serializer(self):
        return self.serializer

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

    def set_case_state_type(self, state_name):
        self.case_state_type, _ = CaseStateType.objects.get_or_create(
            name=state_name,
        )
        self.save()

    def get_script_engine(self, wf):
        # injects functions in workflow
        workflow_instance = self

        def set_status(input):
            workflow_instance.set_case_state_type(input)

        def wait_for_workflows_and_send_message(message, data={}):
            task_wait_for_workflows_and_send_message.delay(
                workflow_instance.id, message, data
            )

        def script_wait(message, data={}):
            task_script_wait.delay(workflow_instance.id, message, data)

        def start_subworkflow(subworkflow_name, data={}):
            # Filter out non-serializable objects (like functions) from the data
            def clean_data_for_serialization(obj):
                if isinstance(obj, dict):
                    return {
                        k: clean_data_for_serialization(v)
                        for k, v in obj.items()
                        if not callable(v) and k != "__builtins__"
                    }
                elif isinstance(obj, (list, tuple)):
                    return [clean_data_for_serialization(item) for item in obj]
                elif callable(obj):
                    return None  # Skip function objects
                else:
                    return obj

            cleaned_data = clean_data_for_serialization(data)
            task_start_subworkflow.delay(
                subworkflow_name, workflow_instance.id, cleaned_data
            )

        def parse_duration_string(str_duration):
            # Convert to timedelta if it's a string
            if isinstance(str_duration, datetime.timedelta):
                td = str_duration
            else:
                td = parse_duration(str_duration)

            # Always return ISO 8601 duration format for SpiffWorkflow compatibility
            if td is not None:
                return timedelta_to_iso_duration(td)
            return str_duration  # Return original if parsing failed

        def get_data(field_name):
            data_source = None
            if wf.last_task and getattr(wf.last_task, "data", None):
                data_source = wf.last_task.data
            elif self.data:
                data_source = self.data
            else:
                data_source = {}
            return (
                data_source.get(field_name, {}).get("value")
                if isinstance(data_source.get(field_name), dict)
                else data_source.get(field_name)
            )

        wf.script_engine = PythonScriptEngine(
            environment=TaskDataEnvironment(
                environment_globals={
                    "set_status": set_status,
                    "wait_for_workflows_and_send_message": wait_for_workflows_and_send_message,
                    "script_wait": script_wait,
                    "start_subworkflow": start_subworkflow,
                    "parse_duration": parse_duration_string,
                    "get_data": get_data,
                }
            )
        )
        return wf

    # legacy method, should be removed if all directors use version >=1.0.0
    def handle_message_catch_event_next_step(self, workflow_instance):
        return self.handle_message_wait_for_summons(workflow_instance)

    def handle_citizen_report_feedback_3(self, extra_data={}):
        data = {}
        data.update(extra_data)

        force_citizen_report_feedback = bool(
            data.get("force_citizen_report_feedback", {}).get("value")
        )

        task_completed = data.get("2_feedback", {}).get("value") is True

        if force_citizen_report_feedback or task_completed:
            return data
        return False

    def handle_citizen_report_feedback_2(self, extra_data={}):
        data = {}
        data.update(extra_data)

        feedback_period_exeeded = False

        if data.get("1_feedback", {}).get("value") is True:
            feedback_period_exeeded = (
                self.date_modified
                + parse_duration(data.get("CITIZEN_REPORT_FEEDBACK_SECOND_PERIOD"))
            ) < timezone.now()

        force_citizen_report_feedback = bool(
            data.get("force_citizen_report_feedback", {}).get("value")
        )

        if feedback_period_exeeded or force_citizen_report_feedback:
            return data
        return False

    def handle_citizen_report_feedback_1(self, extra_data={}):
        data = {}
        data.update(extra_data)

        feedback_period_exeeded = (
            self.date_modified
            + parse_duration(data.get("CITIZEN_REPORT_FEEDBACK_FIRST_PERIOD"))
        ) < timezone.now()

        force_citizen_report_feedback = bool(
            data.get("force_citizen_report_feedback", {}).get("value")
        )
        if feedback_period_exeeded or force_citizen_report_feedback:
            return data
        return False

    def handle_message_wait_for_summons(self, workflow_instance):

        message = "message_wait_for_summons"

        # tell the other workfows that this one is waiting
        workflow_instance.data.update(
            {
                message: "done",
            }
        )
        with transaction.atomic():
            workflow_instance.save(update_fields=["data"])
            transaction.on_commit(lambda: workflow_instance.release_lock())

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
            theme = main_workflow.case.theme.snake_case_name

            all_summons = [
                d.get("summon_id")
                for d in all_workflows.values_list("data", flat=True)
                if d.get("summon_id")
            ]
            extra_data = {
                "bepalen_processtap": {
                    "value": "ja" if theme == "ondermijning" else "default"
                },
                "all_summons": all_summons,
                "decision_count": {
                    "value": main_workflow.case.decisions.exclude(
                        decision_type__workflow_option="no_decision"
                    ).count()
                },
                "next_step": {"value": "default"},
                "names": {"value": ""},
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
                        "summon_next_step": {"value": "default"},
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

        success = False
        jump_to = initial_data.pop("jump_to", None)

        if jump_to:
            result = self.reset_subworkflow(jump_to, test=False)
            success = result.get("success")

        if not success:
            wf = self._initial_data(wf, initial_data)

            wf = self._update_workflow(wf)

            if self.workflow_message_name:
                wf.catch(
                    BpmnEvent(
                        # Only the message name is relevant here, the other parameters are not used but the docs don't really specify what they are used for.
                        MessageEventDefinition(self.workflow_message_name),
                        {"result_var": "result_var", "payload": "payload"},
                    )
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
            wf.last_task.data.update(extra_data)

        wf = self._update_workflow(wf)

        wf.catch(
            BpmnEvent(
                # Only the message name is relevant here, the other parameters are not used but the docs don't really specify what they are used for.
                MessageEventDefinition(message_name),
                {"result_var": "result_var", "payload": "payload"},
            )
        )

        wf = self._update_workflow(wf)
        self._update_db(wf)

    def update_workflow_data(self, data={}):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return False

        if wf.last_task:
            wf.last_task.data.update(data)
        for t in wf.last_task.children:
            t.data.update(data)
        self._execute_scripts_if_needed(wf)

        serialize_wf = self.get_serializer().serialize_json(wf)
        self.serialized_workflow_state = serialize_wf

        self.save()
        task_update_workflow.delay(self.id)

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
        ready_tasks_ids = [t.id for t in wf.get_tasks(state=TaskState.READY)]

        # cleanup: sets dj tasks to completed
        task_instances = self.tasks.all().exclude(
            task_id__in=ready_tasks_ids,
        )
        updated = task_instances.update(completed=True)

        return updated

    def _get_task_display_name(self, task):
        """
        Get the display name for a task, handling SpiffWorkflow 3.x API changes.
        Tries multiple approaches to find the proper human-readable task name.
        """
        try:
            # Try SpiffWorkflow 3.x approach first - check for display_name or description
            if hasattr(task.task_spec, "display_name") and task.task_spec.display_name:
                return Template(task.task_spec.display_name).safe_substitute(task.data)

            # Try description (legacy approach)
            if hasattr(task.task_spec, "description") and task.task_spec.description:
                description = task.task_spec.description
                if description and description.strip() and description != "User Task":
                    return Template(description).safe_substitute(task.data)

            # Try task_spec.bpmn_name or bpmn_id (newer SpiffWorkflow versions)
            if hasattr(task.task_spec, "bpmn_name") and task.task_spec.bpmn_name:
                return Template(task.task_spec.bpmn_name).safe_substitute(task.data)

            # Try the name field (technical name, but better than "User Task")
            if hasattr(task.task_spec, "name") and task.task_spec.name:
                # Convert technical name to more readable format
                name = (
                    task.task_spec.name.replace("_", " ").replace("task ", "").title()
                )
                return Template(name).safe_substitute(task.data)

            # Last resort: return a generic name
            return "User Task"

        except Exception as e:
            logger.warning(f"Error getting task display name: {e}")
            return getattr(task.task_spec, "name", "User Task")

    def create_user_tasks(self, wf):
        ready_tasks = wf.get_tasks(state=TaskState.READY)
        task_data = [
            CaseUserTask(
                task_id=task.id,
                task_name=task.task_spec.name,
                name=self._get_task_display_name(task),
                roles=[
                    r.strip()
                    for r in (task.task_spec.lane or "").split(",")
                    if r.strip()
                ],
                form=parse_task_spec_form(getattr(task.task_spec, "form", None)),
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

        # In v3, check if workflow is actually completed
        if wf.is_completed() and not self.completed:
            self.completed = True
            self._update_db(wf)
        elif not wf.is_completed():
            # If workflow is not completed, try to advance it
            wf.refresh_waiting_tasks()
            wf.do_engine_steps()
            if wf.is_completed() and not self.completed:
                self.completed = True
                self._update_db(wf)

    def update_tasks(self, wf):
        self.set_absolete_tasks_to_completed(wf)
        self.create_user_tasks(wf)
        self.complete_sub_workflow(wf)

    # The sub_workflow.bpmn has multiple flows inside, so spiff does not know when the workflow is completed.
    def complete_sub_workflow(self, wf):
        if (
            self.workflow_type == self.WORKFLOW_TYPE_SUB
            and len(wf.get_tasks(state=TaskState.READY)) == 0
        ):
            self.completed = True
            self.save()

    @staticmethod
    def get_task_by_task_id(id):
        task = get_object_or_404(CaseUserTask, id=id)
        return task

    @staticmethod
    def complete_user_task(id, data, wait=False):
        task = task_complete_user_task_and_create_new_user_tasks.delay(id, data)
        if wait:
            task.wait(timeout=None, interval=0.5)

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

        task = wf.get_task_from_id(task_id)

        if task and isinstance(task.task_spec, UserTask):
            task.set_data(**data)
            task.complete()
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
        self.ensure_data_dict()
        if wf.last_task:
            data = wf.last_task.data
            self.data.update(data)

        completed = False
        if wf.is_completed() and not self.completed:
            completed = True
            self.completed = True

        for task in wf.get_tasks():
            if hasattr(task, "data") and task.data:
                task.data = data

        reg = self.get_serializer().configure(CAMUNDA_CONFIG)
        serializer = BpmnWorkflowSerializer(registry=reg)
        state = serializer.serialize_json(wf)
        self.serialized_workflow_state = state
        self.started = True
        self.save()

        if completed:
            data = copy.deepcopy(wf.last_task.data) if wf.last_task else {}
            task_complete_worflow.delay(self.id, data)

    def get_or_restore_workflow_state(self):
        # Get the unserialized workflow from this workflow instance, it has to use an workflow_spec,
        # which in this case will be load from filesystem.
        workflow_spec = self.get_workflow_spec()
        if not workflow_spec:
            return

        if self.serialized_workflow_state:
            try:
                reg = self.get_serializer().configure(CAMUNDA_CONFIG)
                serializer = BpmnWorkflowSerializer(registry=reg)
                wf = serializer.deserialize_json(self.serialized_workflow_state)
                wf = self.get_script_engine(wf)

            except Exception as e:
                logger.error(f"deserialize workflow failed: {e}")
                return False
            return wf
        else:
            wf = BpmnWorkflow(workflow_spec)
            wf = self.get_script_engine(wf)

            # Apply initial data if available
            if self.data:
                if wf.get_tasks(state=TaskState.READY):
                    wf.get_tasks(state=TaskState.READY)[0].data.update(self.data)

            return wf

    def get_task_elapse_datetime(self, task_id, workflow=None):
        if workflow is None:
            workflow = self.get_or_restore_workflow_state()
        if not workflow:
            return

        task = workflow.get_task_from_id(task_id)
        sibling = (
            next(iter([t for t in task.parent.children if t.id != task_id]), None)
            if hasattr(task, "parent")
            else None
        )
        if (
            sibling
            and isinstance(getattr(sibling, "task_spec", None), BoundaryEvent)
            and isinstance(
                getattr(sibling.task_spec, "event_definition", None),
                TimerEventDefinition,
            )
            and getattr(sibling.task_spec, "attached_to", None)
            is getattr(task.parent, "task_spec", None)
        ):
            start_time = datetime.datetime.strptime(
                sibling._get_internal_data("start_time", None), "%Y-%m-%d %H:%M:%S.%f"
            )
            task_datetime = sibling.workflow.script_engine.evaluate(
                sibling, sibling.task_spec.event_definition.dateTime
            )
            # Handle both timedelta objects and ISO 8601 strings
            if isinstance(task_datetime, datetime.timedelta):
                return start_time + task_datetime
            elif isinstance(task_datetime, str):
                # Parse ISO 8601 string to timedelta
                td = parse_duration(task_datetime)
                if td:
                    return start_time + td

    def set_task_elapse_datetime(self, task_id, datetime_new):
        workflow = self.get_or_restore_workflow_state()
        if not workflow:
            return

        task = workflow.get_task(task_id)
        sibling = (
            next(iter([t for t in task.parent.children if t.id != task_id]), None)
            if hasattr(task, "parent")
            else None
        )
        if (
            sibling
            and isinstance(getattr(sibling, "task_spec", None), BoundaryEvent)
            and isinstance(
                getattr(sibling.task_spec, "event_definition", None),
                TimerEventDefinition,
            )
            and getattr(sibling.task_spec, "attached_to", None)
            is getattr(task.parent, "task_spec", None)
        ):
            task_datetime = sibling.workflow.script_engine.evaluate(
                sibling, sibling.task_spec.event_definition.dateTime
            )
            # Handle both timedelta objects and ISO 8601 strings
            td = None
            if isinstance(task_datetime, datetime.timedelta):
                td = task_datetime
            elif isinstance(task_datetime, str):
                # Parse ISO 8601 string to timedelta
                td = parse_duration(task_datetime)

            if td:
                new_start_time = (datetime_new - td).strftime("%Y-%m-%d %H:%M:%S.%f")
                sibling.internal_data["start_time"] = new_start_time
                self.save_workflow_state(workflow)
                return new_start_time

    def _initial_data(self, wf, data):

        first_task = wf.get_tasks(state=TaskState.READY)
        last_task = wf.last_task
        if first_task:
            first_task = first_task[0]
        elif last_task:
            first_task = last_task

        first_task.data.update(data)

        return wf

    def update_workflow(self):
        # Call this on a regular bases to complete tasks that are time related
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return
        # Change the workflow
        wf = self._update_workflow(wf)

        # No changes to the workflow after this point
        self._update_db(wf)

    def has_a_timer_event_fired(self):
        wf = self.get_or_restore_workflow_state()
        if not wf:
            return False
        waiting_tasks = wf.get_tasks(state=TaskState.WAITING)

        if wf.last_task:
            self._execute_scripts_if_needed(wf)

        for task in waiting_tasks:
            if hasattr(task.task_spec, "event_definition") and isinstance(
                task.task_spec.event_definition, TimerEventDefinition
            ):
                event_definition = task.task_spec.event_definition
                has_fired = event_definition.has_fired(task)
                if has_fired:
                    logger.warning(
                        f"TimerEventDefinition for task '{task.task_spec.name}' has expired. Workflow with id '{self.id}', needs an update"
                    )
                    return True
        return False

    def _execute_scripts_if_needed(self, wf):
        """Execute scripts for message events when there are waiting tasks."""
        waiting_tasks = wf.get_tasks(state=TaskState.WAITING)
        for task in waiting_tasks:
            # Only execute scripts for message events, not regular script tasks
            if hasattr(task.task_spec, "event_definition") and isinstance(
                task.task_spec.event_definition, MessageEventDefinition
            ):
                message = task.task_spec.event_definition.message
                script_tasks = [
                    t for t in wf.get_tasks() if t.task_spec.name == f"script_{message}"
                ]
                if script_tasks:
                    script_task = script_tasks[0]
                    # Get the data to execute the script against
                    data = wf.last_task.data if wf.last_task else {}
                    # Execute the script - it modifies the data dict in place
                    script_task.workflow.script_engine.execute(
                        script_task,
                        script_task.task_spec.script,
                        data,
                    )
                    # The execute method modifies the data dict in place,
                    # but we need to ensure the script_task's data is also updated
                    script_task.data.update(data)

                    # After executing message event scripts, run engine steps to process any changes
                    wf.refresh_waiting_tasks()
                    wf.do_engine_steps()
        return wf

    def _update_workflow(self, wf):
        wf.refresh_waiting_tasks()
        wf.do_engine_steps()
        return wf

    def _update_db(self, wf):
        with transaction.atomic():
            self.save_workflow_state(wf)
            self.update_tasks(wf)
            transaction.on_commit(lambda: self.release_lock())

    def reset_subworkflow(self, subworkflow, test=True):
        wf = self.get_or_restore_workflow_state()
        if hasattr(wf, "last_task") and wf.last_task:
            original_data = copy.deepcopy(wf.last_task.data)
        else:
            original_data = self.data

        latest_theme_name, latest_version = get_latest_version_from_config(
            self.workflow_theme_name, self.workflow_type
        )
        latest_path = get_workflow_path(
            self.workflow_type,
            latest_theme_name,
            latest_version,
        )
        initial_data = get_initial_data_from_config(
            latest_theme_name,
            self.workflow_type,
            latest_version,
            self.workflow_message_name,
        )
        initial_data.update(original_data)
        initial_data.pop("jump_to", None)

        wf_spec_latest = get_workflow_spec(latest_path, self.workflow_type)
        if (
            not self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR
            or subworkflow not in self.SUBWORKFLOWS
        ):
            return {"success": False}

        workflow_result, success = ff_to_subworkflow(
            subworkflow, wf_spec_latest, self.workflow_message_name, initial_data
        )
        if success:

            subworkflows_to_be_deleted = CaseWorkflow.objects.filter(
                parent_workflow=self
            )
            tasks_to_be_deleted = CaseUserTask.objects.filter(
                workflow__in=subworkflows_to_be_deleted
            )

        result = {
            "success": success,
            "data": initial_data,
        }

        if not success:
            result.update(
                {
                    "message": "Op basis van de huidige data van deze director, kun je niet resetten naar de gekozen workflow"
                }
            )
            return result

        if test:

            result.update(
                {
                    "current_version": self.workflow_version,
                    "new_version": latest_version,
                    "current_theme_name": self.workflow_theme_name,
                    "new_theme_name": latest_theme_name,
                    "subworkflows_to_be_deleted": subworkflows_to_be_deleted,
                    "tasks_to_be_deleted": tasks_to_be_deleted,
                    "subworkflow": subworkflow,
                    "data": initial_data,
                }
            )
            return result
        else:
            state = self.get_serializer().serialize_workflow(
                workflow_result.get("workflow"), include_spec=False
            )
            self.workflow_theme_name = latest_theme_name
            self.workflow_version = latest_version
            self.serialized_workflow_state = state
            with transaction.atomic():
                self.save()
                subworkflows_to_be_deleted.delete()
                transaction.on_commit(
                    lambda: task_start_subworkflow.delay(subworkflow, self.id)
                )
            return result

    def migrate_to_version(self, workflow_version, test=True):
        wf = self.get_or_restore_workflow_state()
        if not self.parent_workflow or not wf:
            return False

        original_data = copy.deepcopy(wf.last_task.data) if wf.last_task else {}
        expected_user_task_names = [
            t.task_spec.name
            for t in wf.get_tasks(state=TaskState.READY)
            if isinstance(t.task_spec, UserTask)
        ]

        # manual override of expected tasks for version 2.0.0
        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DEBRIEF and sorted(
            expected_user_task_names
        ) == sorted(
            [
                "task_create_concept_summons",
                "task_create_picture_rapport",
                "task_create_report_of_findings",
            ]
        ):
            expected_user_task_names = [
                "task_create_picture_rapport",
                "task_create_report_of_findings",
            ]
        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DEBRIEF and sorted(
            expected_user_task_names
        ) == sorted(["task_create_concept_summons"]):
            expected_user_task_names = ["task_terugkoppelen_melder_2"]
        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DEBRIEF and sorted(
            expected_user_task_names
        ) == sorted(["task_create_concept_summons", "task_create_report_of_findings"]):
            expected_user_task_names = ["task_create_report_of_findings"]
        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DEBRIEF and sorted(
            expected_user_task_names
        ) == sorted(
            [
                "task_check_summons",
            ]
        ):
            expected_user_task_names = ["task_terugkoppelen_melder_2"]
        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DEBRIEF and sorted(
            expected_user_task_names
        ) == sorted(
            [
                "task_terugkoppelen_melder_1",
            ]
        ):
            expected_user_task_names = [
                "task_terugkoppelen_melder_1",
                "task_prepare_abbreviated_visit_rapport",
            ]

        for case_user_task in CaseUserTask.objects.filter(
            workflow=self,
            task_name__in=expected_user_task_names,
            workflow__parent_workflow__isnull=False,
            completed=False,
            due_date__isnull=False,
        ):
            cached_task_key = f"parent_workflow_{case_user_task.workflow.parent_workflow.id}_{case_user_task.task_name}_due_date"
            cache.set(
                cached_task_key,
                {
                    "due_date": case_user_task.due_date,
                    "owner": case_user_task.owner,
                },
                60 * 60,
            )

        latest_theme_name, latest_version = get_latest_version_from_config(
            self.workflow_theme_name, self.workflow_type, workflow_version
        )
        latest_path = get_workflow_path(
            self.workflow_type,
            self.workflow_theme_name,
            latest_version,
        )
        initial_data = get_initial_data_from_config(
            latest_theme_name,
            self.workflow_type,
            latest_version,
            self.workflow_message_name,
        )

        initial_data.update(original_data)

        if self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_VISIT:
            initial_data.update(
                {
                    "bepalen_processtap": {
                        "value": "ja" if self.case.theme.id == 4 else "default"
                    },
                }
            )

        wf_spec_latest = get_workflow_spec(latest_path, self.workflow_type)

        current_workflow = self.get_or_restore_workflow_state()
        timer_event_task_start_times = dict(
            (t.task_spec.name, t.internal_data.get("start_time"))
            for t in current_workflow.task_tree
            if t.internal_data.get("start_time")
        )

        workflow = ff_workflow(
            wf_spec_latest,
            initial_data,
            expected_user_task_names,
            timer_event_task_start_times,
        )

        result = {
            "workflow": workflow,
            "workflow_type": self.workflow_type,
            "current_workflow": current_workflow,
            "found_user_task_names": (
                [
                    t.task_spec.name
                    for t in workflow.get_tasks(state=TaskState.READY)
                    if isinstance(t.task_spec, UserTask)
                ]
                if workflow
                else []
            ),
            "expected_user_task_names": expected_user_task_names,
            "current_version": self.workflow_version,
            "latest_version": latest_version,
            "current_theme_name": self.workflow_theme_name,
            "latest_theme_name": latest_theme_name,
        }
        return result, bool(workflow)

    def migrate_to_latest(self, test=True):
        success = False
        result = {}
        if not self.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR:
            return {"workflow_result": "Not a director"}, False
        if self.case.end_date:
            return {"workflow_result": "Case is closed"}, False
        wf = self.get_or_restore_workflow_state()
        if not wf:
            original_data = self.data
        else:
            original_data = (
                copy.deepcopy(wf.last_task.data) if wf.last_task else self.data
            )

        subworkflows = CaseWorkflow.objects.filter(
            parent_workflow=self, completed=False
        )
        if subworkflows.count() != 1:
            return {"subworkflow_count": subworkflows.count()}, False
        subworkflow = subworkflows.first()

        latest_theme_name, latest_version = get_latest_version_from_config(
            self.workflow_theme_name, self.workflow_type
        )
        latest_path = get_workflow_path(
            self.workflow_type,
            latest_theme_name,
            latest_version,
        )
        initial_data = get_initial_data_from_config(
            latest_theme_name,
            self.workflow_type,
            latest_version,
            self.workflow_message_name,
        )
        initial_data.update(original_data)

        wf_spec_latest = get_workflow_spec(latest_path, self.workflow_type)

        workflow_result, workflow_success = ff_to_subworkflow(
            subworkflow.workflow_type,
            wf_spec_latest,
            self.workflow_message_name,
            initial_data,
        )
        workflow_result.update(
            {
                "current_version": self.workflow_version,
                "latest_version": latest_version,
                "current_theme_name": self.workflow_theme_name,
                "latest_theme_name": latest_theme_name,
            }
        )
        result.update(
            {
                "workflow_result": workflow_result,
                "subworkflow_result": None,
            }
        )
        subworkflow_result = {}
        if workflow_success:
            subworkflow_result, subworkflow_success = subworkflow.migrate_to_version(
                latest_version
            )
            result.update(
                {
                    "subworkflow_result": subworkflow_result,
                }
            )
            if subworkflow_success:
                success = True
        if not test and success:
            state = self.get_serializer().serialize_workflow(
                workflow_result.get("workflow"), include_spec=False
            )
            self.workflow_theme_name = latest_theme_name
            self.workflow_version = latest_version
            self.serialized_workflow_state = state

            subworkflow_state = self.get_serializer().serialize_workflow(
                subworkflow_result.get("workflow"), include_spec=False
            )
            subworkflow.workflow_theme_name = subworkflow_result.get(
                "latest_theme_name"
            )
            subworkflow.workflow_version = subworkflow_result.get("latest_version")
            subworkflow.serialized_workflow_state = subworkflow_state

            with transaction.atomic():
                self.save()
                subworkflow.save()
                CaseUserTask.objects.filter(workflow=subworkflow).delete()
                transaction.on_commit(
                    lambda: task_update_workflow.delay(subworkflow.id)
                )

        return result, success

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
    enabled_on_case_closed = models.BooleanField(default=False)

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
    task_name = models.CharField(
        max_length=255,
    )
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
