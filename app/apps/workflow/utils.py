import copy
import json
import logging
import os

from deepdiff import DeepDiff
from prettyprinter import pprint
from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.specs.StartTask import StartTask
from SpiffWorkflow.task import Task

logger = logging.getLogger(__name__)


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


def get_latest_version(workflow_type, theme_name="default"):
    def get_path(_theme_name):
        return os.path.join(
            get_base_path(),
            "bpmn_files",
            _theme_name.lower(),
            workflow_type.lower(),
        )

    def get_dirs(path):
        return (
            sorted([o for o in os.listdir(path) if not os.path.isfile(o)])
            if os.path.exists(path)
            else []
        )

    versions = get_dirs(get_path(theme_name))
    if not versions:
        theme_name = "default"
        versions = get_dirs(get_path(theme_name))
    if versions:
        return theme_name, versions[-1]
    return False, False


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
    get_workflow_spec_dump(spec_a, False, False, "task_beeldverslag_opstellen")

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


def workflow_health_check(workflow_spec, data, expected_user_task_names):
    def set_status(status):
        logger.info(f"set_status: {status}")

    def wait_for_workflows_and_send_message(message):
        logger.info(f"wait_for_workflows_and_send_message: {message}")

    script_engine = BpmnScriptEngine(
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


def main():
    compare_results = compare_workflow_specs(
        "0.1.0", "0.2.0", "vakantieverhuur", "main_workflow"
    )
    logger.info(compare_results)


if __name__ == "__main__":
    main()
