from django.conf import settings
from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.specs.StartTask import StartTask
from SpiffWorkflow.task import Task


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
    print(all_task_ids)
    all_task_ids = [n for n in all_task_ids if n not in spiff_task_names]

    for i in set(all_task_ids):
        all_task_ids.remove(i)
    print(all_task_ids)
    return all_task_ids


def workflow_health_check(data, expected_user_task_names):
    x = CamundaParser()

    def set_status(status):
        print("set_status: %s" % status)

    script_engine = BpmnScriptEngine(
        scriptingAdditions={
            "set_status": set_status,
        }
    )
    workflow_spec = settings.WORKFLOWS.get(settings.DEFAULT_WORKFLOW)
    for f in workflow_spec.get("proccess_files"):
        x.add_bpmn_file(f)
    spec = x.get_spec(workflow_spec.get("main_proccess"))
    workflow = BpmnWorkflow(spec, script_engine=script_engine)

    first_task = workflow.get_tasks(Task.READY)[0]
    first_task.update_data(data)

    workflow.do_engine_steps()
    workflow.message(
        "main_process", settings.DEFAULT_SCHEDULE_ACTIONS[0], "status_name"
    )
    workflow.do_engine_steps()

    print("expected_user_task_names")
    print(expected_user_task_names)
    print("data")
    print(data)

    found_user_task_name = []

    task_mask = Task.READY | Task.WAITING
    # ready_tasks = workflow.get_tasks(task_mask)
    ready_tasks = workflow.get_ready_user_tasks()
    done = False
    while len(ready_tasks) > 0:

        for task in ready_tasks:
            found_user_task_name = [t.task_spec.name for t in ready_tasks]
            print(task.task_spec.name)

            if sorted(found_user_task_name) == sorted(expected_user_task_names):
                # if isinstance(task.task_spec, UserTask):
                print("STOP")
                ready_tasks = []
                # task.update_data(data)
                # workflow.complete_task_from_id(task.id)
                workflow.refresh_waiting_tasks()
                workflow.do_engine_steps()
                print([t.task_spec.name for t in workflow.get_tasks(task_mask)])
                waiting_tasks = workflow.get_tasks(Task.WAITING)

                if waiting_tasks:
                    print(waiting_tasks[-1].__dict__)
                    print(waiting_tasks[-1].parent.__dict__)

                done = True
                break

            if task.task_spec.name not in expected_user_task_names:
                task.update_data(data)
                workflow.complete_task_from_id(task.id)
                workflow.refresh_waiting_tasks()
                workflow.do_engine_steps()
                ready_tasks = workflow.get_ready_user_tasks()

        if not ready_tasks and not done:
            print("Nothing found, have to check for waiting tasks to complete.")
            waiting_tasks = workflow.get_tasks(Task.WAITING)
            if waiting_tasks:
                print(waiting_tasks[-1].task_spec.name)
                print(type(waiting_tasks[-1].task_spec))
                print(waiting_tasks[-1].parent.task_spec.name)
                print(type(waiting_tasks[-1].parent.task_spec))
            for wt in waiting_tasks:
                if isinstance(wt.parent.task_spec, StartTask):
                    pass

    return done
