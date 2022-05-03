import copy
import datetime
import itertools
import json
import logging
import os

from apps.events.models import TaskModelEventEmitter
from deepdiff import DeepDiff
from django.conf import settings
from prettyprinter import pprint
from SpiffWorkflow.bpmn.PythonScriptEngine import PythonScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.specs.BoundaryEvent import BoundaryEvent
from SpiffWorkflow.bpmn.specs.event_definitions import TimerEventDefinition
from SpiffWorkflow.bpmn.specs.ScriptTask import ScriptTask
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.specs.StartTask import StartTask
from SpiffWorkflow.task import Task

logger = logging.getLogger(__name__)


def complete_uncompleted_task_for_event_emitters(event_emmitter, data={}):
    from .models import CaseWorkflow

    if not issubclass(event_emmitter.__class__, TaskModelEventEmitter):
        logger.error(
            f"Not an event emitter: emitter type: {event_emmitter.__class__.__name__}, emitter id: {event_emmitter.id}"
        )
        return
    task = event_emmitter.case.tasks.filter(
        id=int(event_emmitter.case_user_task_id),
        completed=False,
    ).first()
    if not task:
        logger.error(
            f"Task not found or completed: task_id: {event_emmitter.case_user_task_id}, emitter type: {event_emmitter.__class__.__name__}, emitter id: {event_emmitter.id}"
        )
        return

    CaseWorkflow.complete_user_task(event_emmitter.case_user_task_id, {})


def parse_task_spec_form(form):
    trans_types = {
        "enum": "select",
        "boolean": "checkbox",
        "string": "text",
        "long": "number",
    }
    fields = [
        {
            "label": f.label,
            "options": [
                {
                    "value": o.id,
                    "label": o.name,
                }
                for o in f.__dict__.get("options", [])
            ],
            "name": f.id,
            "type": "multiselect"
            if bool([v.name for v in f.validation if v.name == "multiple"])
            else trans_types.get(f.type, "text"),
            "required": not bool(
                [v.name for v in f.validation if v.name == "optional"]
            ),
            "tooltip": next(
                iter([v.value for v in f.properties if v.id == "tooltip"]), None
            ),
        }
        for f in form.fields
    ]
    return fields


def map_variables_on_task_spec_form(variables, task_spec_form):
    # transforms form result data and adds labels for the frontend
    form = dict((f.get("name"), f) for f in task_spec_form)
    return dict(
        (
            k,
            {
                "label": form.get(k, {}).get("label", v.get("value")),
                "value": v.get("value")
                if not form.get(k, {}).get("options")
                else [
                    dict((o.get("value"), o) for o in form.get(k, {}).get("options"))
                    .get(vv, {})
                    .get("label", vv)
                    for vv in v.get("value")
                ]
                if isinstance(v.get("value"), list)
                else dict((o.get("value"), o) for o in form.get(k, {}).get("options"))
                .get(v.get("value"), {})
                .get("label", v.get("value")),
            },
        )
        for k, v in variables.items()
        if isinstance(v, dict)
    )


def check_for_duplicate_task_spec_ids(workflow_spec):
    spiff_task_names = ["Start", "End"]
    all_task_ids = []

    def sub_workflow_task_specs(task_spec, all_task_ids):
        spec = task_spec.__dict__.get("spec")
        if spec:
            for k, v in spec.__dict__.get("task_specs").items():
                all_task_ids.append(k)
                sub_workflow_task_specs(v, all_task_ids)

    for name, value in workflow_spec.task_specs.items():
        all_task_ids.append(name)
        sub_workflow_task_specs(value, all_task_ids)
    logger.info(all_task_ids)
    all_task_ids = [n for n in all_task_ids if n not in spiff_task_names]

    for i in set(all_task_ids):
        all_task_ids.remove(i)
    logger.info(all_task_ids)
    return all_task_ids


def get_workflow_spec_user_tasks(workflow_spec):
    workflow_specs = workflow_spec.get_specs_depth_first()
    return [
        ts
        for workflow_spec in workflow_specs
        for k, ts in workflow_spec.task_specs.items()
        if isinstance(ts, UserTask)
    ]


def get_base_path():
    return os.path.dirname(os.path.realpath(__file__))


def get_latest_version_from_config(
    theme_name, workflow_type, current_version=None, workflow_spec_config=None
):
    workflow_spec_config = (
        workflow_spec_config if workflow_spec_config else settings.WORKFLOW_SPEC_CONFIG
    )
    validated_workflow_spec_config = validate_workflow_spec(workflow_spec_config)

    config = validated_workflow_spec_config.get(theme_name)
    if not config:
        theme_name = "default"
        config = validated_workflow_spec_config.get(theme_name, {})

    config = config.get(workflow_type, {})
    if not config:
        raise Exception(
            f"Workflow type '{workflow_type}', does not exist in this workflow_spec config"
        )

    def get_major(v):
        return int(v.split(".")[0])

    version = sorted([v for v, k in config.get("versions").items()])

    if current_version:
        version = [v for v in version if get_major(current_version) >= get_major(v)]

    if not version:
        raise Exception(
            f"Workflow version for theme name '{theme_name}', with type '{workflow_type}', does not exist in this workflow_spec config"
        )
    return theme_name, version[-1]


def get_initial_data_from_config(
    theme_name, workflow_type, workflow_version, message_name=None
):
    validated_workflow_spec_config = validate_workflow_spec(
        settings.WORKFLOW_SPEC_CONFIG
    )
    config = validated_workflow_spec_config.get(theme_name)
    if not config:
        theme_name = "default"
        config = validated_workflow_spec_config.get(theme_name, {})

    config = config.get(workflow_type, {})
    if not config:
        raise Exception(
            f"Workflow type '{workflow_type}', does not exist in this workflow_spec config"
        )

    def pre_serialize_timedelta(value):
        if isinstance(value, datetime.timedelta):
            duration = settings.DEFAULT_WORKFLOW_TIMER_DURATIONS.get(
                settings.ENVIRONMENT
            )
            if duration:
                value = duration
            return json.loads(json.dumps(value, default=str))
        return value

    initial_data = config.get("initial_data", {})

    version = config.get("versions", {}).get(workflow_version)
    if (
        message_name
        and version
        and version.get("messages", {}).get(message_name, {}).get("initial_data", {})
    ):
        initial_data = (
            version.get("messages", {}).get(message_name, {}).get("initial_data", {})
        )

    initial_data = dict(
        (k, pre_serialize_timedelta(v)) for k, v in initial_data.items()
    )

    return initial_data


def get_workflow_path(workflow_type, theme_name="default", workflow_version="latest"):
    path = os.path.join(
        get_base_path(),
        "bpmn_files",
        theme_name.lower(),
        workflow_type.lower(),
        workflow_version.lower(),
    )
    return path


def is_bpmn_file(file_name):
    return file_name.split(".")[-1] == "bpmn"


def get_workflow_spec(path, workflow_type):
    x = CamundaParser()

    for f in get_workflow_spec_files(path):
        x.add_bpmn_file(f)
    spec = x.get_spec(workflow_type)
    return spec


def get_workflow_spec_files(path):
    return [
        os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f)) and is_bpmn_file(f)
    ]


def compare_path_until_task(workflow_spec_a, workflow_spec_b, task_name):
    """
    Compares two workflow_specs until a specific task_spec is found
    It compares the paths of the two results
    In this test it compares the list of most of the task_spec items (task_spec.name items, task_spec class and the serialized form)
    If valid is True, it should be save migrate to workflow_spec_b, for this task
    """

    result_a = get_workflow_spec_dump(
        workflow_spec_a,
        hide_names=False,
        show_input_output=False,
        find_task_name=task_name,
    )
    result_b = get_workflow_spec_dump(
        workflow_spec_b,
        hide_names=False,
        show_input_output=False,
        find_task_name=task_name,
    )

    # get path by task_name
    path = [p for p in result_a.get("paths") if p.get("task_name") == task_name]
    if not path or len(path) > 1:
        return False
    path = json.dumps(path[0].get("path"))

    found_path = [p for p in result_b.get("paths") if p.get("task_name") == task_name]
    if not found_path or len(found_path) > 1:
        return False
    found_path = json.dumps(found_path[0].get("path"))
    logger.info(found_path)
    if found_path == path:
        # happy flow, task_name can be renamed to found_path[0]
        return found_path[0]
    return False


def check_task_id_changes(workflow_spec_a, workflow_spec_b, task_name):
    result_a = get_workflow_spec_dump(
        workflow_spec_a,
        hide_names=True,
        show_input_output=False,
        find_task_name=task_name,
    )
    result_b = get_workflow_spec_dump(
        workflow_spec_b,
        hide_names=True,
        show_input_output=False,
        find_task_name=task_name,
    )

    # get path by task_name
    path = [p for p in result_a.get("paths") if p.get("task_name") == task_name]
    if not path or len(path) > 1:
        return False
    path = json.dumps(path[0].get("path"))

    # find path in workflow_spec_b paths
    found_path = [
        p.get("task_name")
        for p in result_b.get("paths")
        if json.dumps(p.get("path")) == path
    ]
    if len(found_path) == 1:
        # happy flow, task_name can be renamed to found_path[0]
        return found_path[0]
    return False


def compare_workflow_specs_by_task_specs(
    workflow_spec_a, workflow_spec_b, task_name_ids
):
    """
    CHECK
    If uncompleted user tasks exist in the new workflow_spec, if so,
    check if the path to this task_spec is the same in the new workflow_spec.

    """

    valid = True
    new_task_name_ids = {}
    for task_name in task_name_ids:

        no_changes_for_this_task = compare_path_until_task(
            workflow_spec_a, workflow_spec_b, task_name
        )
        if no_changes_for_this_task:
            pass
        else:

            task_id_changes = check_task_id_changes(
                workflow_spec_a, workflow_spec_b, task_name
            )
            if not task_id_changes:
                valid = False
            elif task_id_changes != task_name:
                logger.info("START: Probably just a task id change")
                logger.info(task_name)
                logger.info(task_id_changes)
                logger.info("END: Probably just a task id change")
                new_task_name_ids[task_name] = task_id_changes
            elif task_id_changes == task_name:
                new_task_name_ids[task_name] = task_id_changes

    return valid, new_task_name_ids


def get_workflow_spec_dump(
    workflow_spec, hide_names=False, show_input_output=False, find_task_name=None
):
    done = set()
    paths = []

    def recursive_dump(task_spec, indent, path):
        if task_spec in done:
            return (
                "[shown earlier] %s (%s)"
                % (
                    "task_spec" if hide_names else task_spec.name,
                    task_spec.__class__.__name__,
                )
                + "\n"
            )

        done.add(task_spec)

        task_spec_blueprint = {
            "task_spec_class_name": task_spec.__class__.__name__,
            "form": parse_task_spec_form(task_spec.form)
            if hasattr(task_spec, "form")
            else [],
        }
        if not hide_names:
            task_spec_blueprint.update(
                {
                    "task_spec_name": task_spec.name,
                }
            )
        path.append(task_spec_blueprint)
        path_clone = copy.deepcopy(path)

        paths.append(
            {
                "task_name": task_spec.name,
                "path": path_clone,
            }
        )
        dump = (
            "%s (%s)"
            % (
                "task_spec" if hide_names else task_spec.name,
                task_spec.__class__.__name__,
            )
            + "\n"
        )

        if show_input_output:
            if task_spec.inputs:
                dump += (
                    indent
                    + "-  IN: "
                    + ",".join(
                        [
                            "%s" % ("task_spec" if hide_names else t.name)
                            for t in task_spec.inputs
                        ]
                    )
                    + "\n"
                )
            if task_spec.outputs:
                dump += (
                    indent
                    + "- OUT: "
                    + ",".join(
                        [
                            "%s" % ("task_spec" if hide_names else t.name)
                            for t in task_spec.outputs
                        ]
                    )
                    + "\n"
                )
        sub_specs = (
            [task_spec.spec.start] if hasattr(task_spec, "spec") else []
        ) + task_spec.outputs
        for i, t in enumerate(sub_specs):
            dump += (
                indent
                + "   --> "
                + recursive_dump(
                    t,
                    indent + ("   |   " if i + 1 < len(sub_specs) else "       "),
                    path,
                )
            )
        return dump

    dump = recursive_dump(workflow_spec.start, "", [])

    return {
        "dump": dump,
        "paths": paths,
    }


def deep_inspect_workflow_spec(workflow_spec):
    pass


def compare_workflow_specs(version_a, version_b, theme_name, worflow_type):
    task_ids_and_stucture_changed = True
    stucture_changed = True
    path_a = get_workflow_path(
        worflow_type,
        theme_name,
        version_a,
    )
    path_b = get_workflow_path(
        worflow_type,
        theme_name,
        version_b,
    )
    spec_a = get_workflow_spec(path_a, worflow_type)
    spec_b = get_workflow_spec(path_b, worflow_type)

    task_specs_a = get_workflow_spec_user_tasks(spec_a)
    task_specs_b = get_workflow_spec_user_tasks(spec_b)

    form_fields_a = [
        f.get("name") for ts in task_specs_a for f in parse_task_spec_form(ts.form)
    ]
    form_fields_b = [
        f.get("name") for ts in task_specs_b for f in parse_task_spec_form(ts.form)
    ]
    user_tasks_changed = DeepDiff(
        [t.name for t in task_specs_a], [t.name for t in task_specs_b]
    )
    user_tasks_formfields_changed = DeepDiff(form_fields_a, form_fields_b)

    logger.info("COMPARE DUMPS")
    if get_workflow_spec_dump(spec_a, True, True).get("dump") == get_workflow_spec_dump(
        spec_b, True, True
    ).get("dump"):
        stucture_changed = False

    if get_workflow_spec_dump(spec_a) == get_workflow_spec_dump(spec_b):
        task_ids_and_stucture_changed = False

    if not bool(user_tasks_formfields_changed):
        deep_inspect_workflow_spec(spec_a)

    logger.info("FORM FIELDS DIFF")
    pprint(bool(user_tasks_formfields_changed))

    logger.info("TASK NAMES DIFF")
    pprint(user_tasks_changed)
    logger.info(form_fields_a)
    return {
        "stucture_changed": stucture_changed,
        "task_ids_and_stucture_changed": task_ids_and_stucture_changed,
        "user_tasks_changed": user_tasks_changed if user_tasks_changed else False,
        "user_tasks_formfields_changed": user_tasks_formfields_changed
        if user_tasks_formfields_changed
        else False,
    }


def get_formfield_ids(task):
    form = task.task_spec.form
    return [field.id for field in form.fields]


def ff_workflow(
    spec,
    data,
    expected_user_task_names,
    timer_event_task_start_times={},
    message_name=None,
):
    script_engine = PythonScriptEngine(
        scriptingAdditions={
            "set_status": lambda *args: None,
            "wait_for_workflows_and_send_message": lambda *args: None,
            "script_wait": lambda *args: None,
            "start_subworkflow": lambda *args: None,
            "parse_duration": lambda *args: None,
        }
    )
    workflow = BpmnWorkflow(spec, script_engine=script_engine)

    first_task = workflow.get_tasks(Task.READY)[0]
    first_task.update_data(data)

    workflow.refresh_waiting_tasks()
    workflow.do_engine_steps()

    if message_name:
        logger.info(f" - message: {message_name}")
        workflow.message(message_name, message_name, "message_name")
        workflow.refresh_waiting_tasks()
        workflow.do_engine_steps()

    def complete_task_and_get_workflow_clone(wf, user_task_data, user_task):
        data = copy.deepcopy(wf.last_task.data)
        data.update(user_task_data)
        workflow_clone_serialized = BpmnSerializer().serialize_workflow(
            wf, include_spec=True
        )
        workflow_clone = BpmnSerializer().deserialize_workflow(
            workflow_clone_serialized
        )
        workflow_clone.script_engine = script_engine
        if user_task:
            tasks = workflow_clone.get_tasks_from_spec_name(user_task.task_spec.name)
            if tasks:
                completed_tasks.append(tasks[0].task_spec.name)
                tasks[0].update_data(data)
                workflow_clone.complete_task_from_id(tasks[0].id)
                try:
                    workflow_clone.refresh_waiting_tasks()
                    workflow_clone.do_engine_steps()
                    return workflow_clone
                except Exception as e:
                    print(e)

    completed_tasks = []

    def check_tasks_found(wf):
        found_user_task_names = [t.task_spec.name for t in wf.get_ready_user_tasks()]
        return sorted(found_user_task_names) == sorted(expected_user_task_names)

    def get_ready_tasks(wf):
        return [
            t
            for t in wf.get_tasks(Task.WAITING | Task.READY)
            if t.task_spec.name not in completed_tasks
            and (
                isinstance(t.task_spec, UserTask)
                or isinstance(t.task_spec, BoundaryEvent)
            )
            and not isinstance(t.task_spec.inputs[0], StartTask)
            or hasattr(t.task_spec, "event_definition")
            and isinstance(t.task_spec.event_definition, TimerEventDefinition)
        ]

    def start_workflow(wf=None):
        ready_tasks = []
        if wf:
            ready_tasks = get_ready_tasks(wf)

        for task in ready_tasks:
            if timer_event_task_start_times.get(task.task_spec.name, None) is not None:
                task.internal_data["start_time"] = timer_event_task_start_times.get(
                    task.task_spec.name
                )

        for task in ready_tasks:
            if check_tasks_found(wf):
                ready_tasks = []
                return wf
            if task.task_spec.name not in expected_user_task_names:
                result_wf = start_workflow(
                    complete_task_and_get_workflow_clone(
                        wf,
                        data,
                        task,
                    )
                )
                if result_wf:
                    return result_wf

    return start_workflow(workflow)


def ff_to_subworkflow(subworkflow, spec, message_name, data):
    script_engine = PythonScriptEngine(
        scriptingAdditions={
            "set_status": lambda *args: None,
            "wait_for_workflows_and_send_message": lambda *args: None,
            "script_wait": lambda *args: None,
            "start_subworkflow": lambda *args: None,
            "parse_duration": lambda *args: None,
        }
    )
    workflow = BpmnWorkflow(spec, script_engine=script_engine)

    first_task = workflow.get_tasks(Task.READY)[0]
    first_task.update_data(data)

    workflow.refresh_waiting_tasks()
    workflow.do_engine_steps()

    workflow.message(message_name, message_name, "message_name")
    workflow.refresh_waiting_tasks()
    workflow.do_engine_steps()

    def get_waiting_tasks(wf):
        return [
            t
            for t in wf.get_tasks(Task.WAITING)
            if t.task_spec.inputs and not isinstance(t.task_spec.inputs[0], StartTask)
        ]

    ready_tasks = get_waiting_tasks(workflow)
    completed = []
    success = False
    while len(ready_tasks) > 0:
        for task in ready_tasks:
            if (
                task.task_spec.description == f"resume_after_{subworkflow}"
                and isinstance(workflow.last_task.task_spec, ScriptTask)
                and workflow.last_task.task_spec.script
                == f'start_subworkflow("{subworkflow}", vars())'
            ):
                ready_tasks = []
                success = True
            else:
                if (
                    task.task_spec.inputs
                    and not isinstance(task.task_spec.inputs[0], StartTask)
                    and task.task_spec.description not in completed
                ):
                    try:
                        task.update_data(data)
                        workflow.complete_task_from_id(task.id)
                        workflow.refresh_waiting_tasks()
                        workflow.do_engine_steps()
                        completed.append(task.task_spec.description)
                        ready_tasks = get_waiting_tasks(workflow)
                    except Exception as e:
                        ready_tasks = []
                        logger.error(f"ERROR: Reset subworkflows: {e}")
                else:
                    ready_tasks = []

    result = {
        "workflow": workflow,
        "last_task_spec_name": workflow.last_task.task_spec.name
        if workflow.last_task
        else None,
        "completed": completed,
    }
    return result, success


def workflow_health_check(workflow_spec, data, expected_user_task_names):
    def set_status(status):
        logger.info(f"set_status: {status}")

    def wait_for_workflows_and_send_message(message):
        logger.info(f"wait_for_workflows_and_send_message: {message}")

    script_engine = PythonScriptEngine(
        scriptingAdditions={
            "set_status": set_status,
            "wait_for_workflows_and_send_message": wait_for_workflows_and_send_message,
        }
    )

    workflow = BpmnWorkflow(workflow_spec, script_engine=script_engine)

    first_task = workflow.get_tasks(Task.READY)[0]
    first_task.update_data(data)

    workflow.do_engine_steps()
    workflow.message("start_signal_process", {"value": "test"}, "next_step")
    workflow.do_engine_steps()

    logger.info("expected_user_task_names")
    logger.info(expected_user_task_names)
    logger.info("data")
    logger.info(data)

    found_user_task_name = []
    missing_form_data = []

    ready_tasks = workflow.get_ready_user_tasks()
    success = False
    logger.info(ready_tasks)
    while len(ready_tasks) > 0:

        for task in ready_tasks:
            found_user_task_name = [t.task_spec.name for t in ready_tasks]
            logger.info(task.task_spec.name)

            if sorted(found_user_task_name) == sorted(expected_user_task_names):

                logger.info("STOP")

                workflow.refresh_waiting_tasks()
                workflow.do_engine_steps()

                waiting_tasks = workflow.get_tasks(Task.WAITING)

                if waiting_tasks:
                    logger.info(waiting_tasks[-1].__dict__)
                    logger.info(waiting_tasks[-1].parent.__dict__)

                ready_tasks = []
                success = True
                break

            if task.task_spec.name not in expected_user_task_names:
                formfield_ids = sorted(get_formfield_ids(task))
                data_keys = list(data.keys())
                missing_keys = sorted([i for i in formfield_ids if i not in data_keys])
                logger.info("CHECK IF FIELD NAMES EXIST IN THE DATA KEYS")
                logger.info("missing_keys")
                logger.info(missing_keys)
                if missing_keys:
                    missing_form_data.append(
                        {
                            "task_name": task.task_spec.name,
                            "keys": [k for k in missing_keys],
                        }
                    )
                    for mk in missing_keys:
                        data.update(
                            {
                                mk: "VALUE_FOR_MISSING_KEY",
                            }
                        )
                task.update_data(data)
                workflow.complete_task_from_id(task.id)
                workflow.refresh_waiting_tasks()
                workflow.do_engine_steps()
                ready_tasks = workflow.get_ready_user_tasks()

        if not ready_tasks and not success:
            logger.info(
                "Nothing found, have to check for waiting tasks to complete. Try to run further when waiting tasks are completed"
            )
            waiting_tasks = workflow.get_tasks(Task.WAITING)
            if waiting_tasks:
                logger.info(waiting_tasks[-1].task_spec.name)
                logger.info(type(waiting_tasks[-1].task_spec))
                logger.info(waiting_tasks[-1].parent.task_spec.name)
                logger.info(type(waiting_tasks[-1].parent.task_spec))
            for wt in waiting_tasks:
                if isinstance(wt.parent.task_spec, StartTask):
                    pass
                else:
                    workflow.complete_task_from_id(wt.id)
                    workflow.refresh_waiting_tasks()
                    workflow.do_engine_steps()
                    ready_tasks = workflow.get_ready_user_tasks()

    return {
        "success": success,
        "missing_form_data": missing_form_data,
        "result_data": data,
    }


def workflow_test_message(message, workflow_spec, script_engine, initial_data={}):
    try:

        workflow_a = BpmnWorkflow(workflow_spec)
        first_task_a = workflow_a.get_tasks(Task.READY)
        first_task_a[0].update_data(initial_data)
        workflow_a_serialized = BpmnSerializer().serialize_workflow(
            workflow_a, include_spec=False
        )
        workflow_b = BpmnSerializer().deserialize_workflow(
            workflow_a_serialized, workflow_spec
        )
        first_task_b = workflow_a.get_tasks(Task.READY)
        first_task_b[0].update_data(initial_data)
        workflow_a.script_engine = script_engine
        workflow_b.script_engine = script_engine

        workflow_a.refresh_waiting_tasks()
        workflow_b.refresh_waiting_tasks()
        workflow_a.do_engine_steps()
        workflow_b.do_engine_steps()

        workflow_a.message(message, "default", "default")

        dump_a = workflow_a.get_dump()
        dump_b = workflow_b.get_dump()

        return dump_a != dump_b
    except Exception:
        return False


def workflow_tree_inspect(
    workflow_org, initial_data, script_engine, message_name=None, spec_user_tasks=[]
):
    workflow_serialized = BpmnSerializer().serialize_workflow(
        workflow_org, include_spec=True
    )
    workflow = BpmnSerializer().deserialize_workflow(workflow_serialized)
    workflow.script_engine = script_engine

    def get_valid_fields(user_task):
        form = parse_task_spec_form(user_task.task_spec.form)
        valid_fields = [f for f in form if f.get("type") in ("select", "checkbox")]
        return valid_fields

    def get_branchs_data(fields):
        out = []
        branches = []

        # flatten field types
        data = dict(
            (
                f.get("name"),
                [option.get("value") for option in f.get("options", [])]
                if f.get("options", [])
                else [True, False],
            )
            for f in fields
        )

        # create unique string by json dumps
        branches = [[json.dumps({k: {"value": o}}) for o in v] for k, v in data.items()]

        # calculate all combinations
        unique_combinations = list(itertools.product(*branches))

        # unpack strings by json loads and combin dicts
        for uc in unique_combinations:
            o = {}
            for u in uc:
                o.update(json.loads(u))
            out.append(o)
        return out

    tasks = workflow.get_tasks(Task.READY)
    if tasks:
        tasks[0].update_data(initial_data)
    workflow.refresh_waiting_tasks()
    workflow.do_engine_steps()

    if message_name:
        logger.info(f" - message: {message_name}")
        workflow.message(message_name, message_name, "message_name")
        workflow.refresh_waiting_tasks()
        workflow.do_engine_steps()

    def complete_task_and_get_workflow_clone(workflow, user_task_data, user_task):
        data = copy.deepcopy(workflow.last_task.data)
        data.update(user_task_data)
        workflow_clone_serialized = BpmnSerializer().serialize_workflow(
            workflow, include_spec=True
        )
        workflow_clone = BpmnSerializer().deserialize_workflow(
            workflow_clone_serialized
        )
        workflow_clone.script_engine = script_engine
        if user_task:
            tasks = workflow_clone.get_tasks_from_spec_name(user_task.task_spec.name)
            if tasks:
                tasks[0].update_data(data)
                workflow_clone.complete_task_from_id(tasks[0].id)
                workflow_clone.refresh_waiting_tasks()
                workflow_clone.do_engine_steps()
                completed_tasks.append(tasks[0].task_spec.name)
        return workflow_clone

    completed_tasks = []

    def start_workflow(workflow):
        ready_tasks = [
            t
            for t in workflow.get_ready_user_tasks()
            if t.task_spec.name not in completed_tasks
        ]
        while len(ready_tasks) > 0:
            for task in ready_tasks:
                fields = []
                if task.task_spec.form:
                    fields = get_valid_fields(task)

                if fields:
                    branches = get_branchs_data(fields)
                    for b in branches:
                        start_workflow(
                            complete_task_and_get_workflow_clone(
                                workflow,
                                b,
                                task,
                            )
                        )
                else:
                    workflow.complete_task_from_id(task.id)
                    workflow.refresh_waiting_tasks()
                    workflow.do_engine_steps()
                    completed_tasks.append(task.task_spec.name)
                ready_tasks = [
                    t
                    for t in workflow.get_ready_user_tasks()
                    if t.task_spec.name not in completed_tasks
                ]

    try:
        start_workflow(workflow)
        completed_tasks = list(set(completed_tasks))
        converage = (
            0
            if not len(spec_user_tasks)
            else round((len(completed_tasks) / len(spec_user_tasks) * 100), 1)
        )
        logger.info(f"User task coverage: {converage}%")
        return f"User task coverage: {converage}%"
    except Exception as e:
        logger.error(str(e))
        return False


def workflow_spec_path_inspect(
    workflow_spec_path, type, script_engine, messages={}, initial_data={}
):
    try:
        workflow_spec = get_workflow_spec(workflow_spec_path, type)
        workflow = BpmnWorkflow(workflow_spec)
        workflow.script_engine = script_engine
        logger.info(f"workflow_type: {type}")
        spec_user_tasks = [
            user_task for user_task in get_workflow_spec_user_tasks(workflow_spec)
        ]
        return {
            "workflow": workflow,
            "forms": [
                parse_task_spec_form(user_task.form) for user_task in spec_user_tasks
            ],
            "messages": [
                {
                    "message": m,
                    "exists": workflow_test_message(
                        m,
                        workflow_spec,
                        script_engine,
                        initial_data
                        if not v.get("initial_data")
                        else v.get("initial_data", {}),
                    ),
                    "tree_valid": workflow_tree_inspect(
                        workflow,
                        initial_data
                        if not v.get("initial_data")
                        else v.get("initial_data", {}),
                        script_engine,
                        m,
                        spec_user_tasks,
                    ),
                }
                for m, v in messages.items()
            ],
            "tree_valid": workflow_tree_inspect(
                workflow, initial_data, script_engine, None, spec_user_tasks
            ),
        }
    except Exception as e:
        logger.error(
            f"ERROR: workflow_spec_path_inspect: path '{workflow_spec_path}', type '{type}', {str(e)}"
        )
        return False


def workflow_spec_paths_inspect(workflow_spec_conf):
    base_path = os.path.join(get_base_path(), "bpmn_files")

    def set_status(status):
        pass

    def wait_for_workflows_and_send_message(message):
        pass

    def script_wait(message, data={}):
        pass

    def start_subworkflow(subflow, data={}):
        pass

    def parse_duration_string(duration_str):
        pass

    script_engine = PythonScriptEngine(
        scriptingAdditions={
            "set_status": set_status,
            "wait_for_workflows_and_send_message": wait_for_workflows_and_send_message,
            "script_wait": script_wait,
            "start_subworkflow": start_subworkflow,
            "parse_duration": parse_duration_string,
        }
    )
    paths = [
        {
            "path": os.path.join(base_path, theme, type, version),
            "workflow_data": workflow_spec_path_inspect(
                os.path.join(base_path, theme, type, version),
                type,
                script_engine,
                version_value.get("messages", {}),
                theme_type.get("initial_data", {}),
            ),
            "theme": theme,
            "type": type,
            "version": version,
            "messages": version_value.get("messages", {}),
        }
        for theme, types in workflow_spec_conf.items()
        for type, theme_type in types.items()
        for version, version_value in theme_type.get("versions", {}).items()
    ]
    return paths


def validate_workflow_spec(workflow_spec_config):
    from .serializers import WorkflowSpecConfigSerializer

    serializer = WorkflowSpecConfigSerializer(data=workflow_spec_config)
    if serializer.is_valid():
        pass
    else:
        raise Exception(
            {
                "message": "settings WORKFLOW_SPEC_CONFIG not valid",
                "details": serializer.errors,
            }
        )
    return serializer.data


def workflow_specs_inspect(workflow_spec_config):
    report = {}
    validated_workflow_spec_config = validate_workflow_spec(workflow_spec_config)

    paths = workflow_spec_paths_inspect(validated_workflow_spec_config)

    non_valid_paths = [p.get("path") for p in paths if not p.get("workflow_data")]
    if non_valid_paths:
        raise Exception(
            {
                "message": "missing paths",
                "details": non_valid_paths,
            }
        )

    report.update(
        {
            "non_valid_paths": [
                p.get("path") for p in paths if not p.get("workflow_spec")
            ],
            "valid_workflow_spec_configs": [p for p in paths if p.get("workflow_spec")],
        }
    )
    pprint(report)


def main():
    compare_results = compare_workflow_specs(
        "0.1.0", "0.2.0", "vakantieverhuur", "main_workflow"
    )
    logger.info(compare_results)


if __name__ == "__main__":
    main()
