import os

from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import EnumFormField, UserTask


def show_form(task):
    form = task.task_spec.form
    task.task_spec.documentation

    # template = Template(docs)
    print(task.data)
    # print(template.render(task.data))

    if task.data is None:
        task.data = {}

    for field in form.fields:
        prompt = field.label
        if isinstance(field, EnumFormField):
            prompt += (
                "? (Options: "
                + ", ".join([str(option.id) for option in field.options])
                + ")"
            )
        prompt += "? "
        answer = input(prompt)
        if field.type == "long":
            answer = int(answer)
        task.update_data_var(field.id, answer)


def main():
    x = CamundaParser()
    # x.add_bpmn_file('test_script_injection_restore.bpmn')
    x.add_bpmn_file("top_workflow.bpmn")
    x.add_bpmn_file("common_workflow.bpmn")
    spec = x.get_spec("top_workflow")

    if os.path.exists("ExampleSaveRestore.js"):
        f = open("ExampleSaveRestore.js")
        state = f.read()
        f.close()
        workflow = BpmnSerializer().deserialize_workflow(state, workflow_spec=spec)
    else:

        workflow = BpmnWorkflow(spec)

    def set_state(value):
        print("set status dus: %s" % value)

    script_engine = BpmnScriptEngine(
        scriptingAdditions={
            "set_state": set_state,
            "set_status": set_state,
        }
    )
    workflow.script_engine = script_engine

    workflow.do_engine_steps()
    ready_tasks = workflow.get_ready_user_tasks()
    while len(ready_tasks) > 0:
        for task in ready_tasks:
            if isinstance(task.task_spec, UserTask):
                show_form(task)
                print(task.data)
            else:
                print("Complete Task ", task.task_spec.name)
            workflow.complete_task_from_id(task.id)
            state = BpmnSerializer().serialize_workflow(workflow, include_spec=True)
            f = open("ExampleSaveRestore.js", "w")
            f.write(state)
            f.close()
        workflow.do_engine_steps()
        ready_tasks = workflow.get_ready_user_tasks()
    print(workflow.last_task.data)


if __name__ == "__main__":
    main()
