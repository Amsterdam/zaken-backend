import os

from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import EnumFormField, UserTask

x = CamundaParser()
x.add_bpmn_file("aza_wonen_global_afronden_zaak.bpmn")
x.add_bpmn_file("aza_wonen_global_voornemen_afzien.bpmn")
x.add_bpmn_file("aza_wonen_global_decision.bpmn")
x.add_bpmn_file("aza_wonen_global_summon.bpmn")
x.add_bpmn_file("aza_wonen_global_visit.bpmn")
x.add_bpmn_file("aza_wonen_local_vakantieverhuur_regie.bpmn")
s = x.get_spec("aza_wonen_local_vakantieverhuur_regie")


def set_status(value):
    print("set status dus: %s" % value)


def set_variable(value):
    return value


class CustomBpmnScriptEngine(BpmnScriptEngine):
    """This is a custom script processor that can be easily injected into Spiff Workflow.
    It will execute python code read in from the bpmn.  It will also make any scripts in the
     scripts directory available for execution."""

    def execute(self, task, script, data):
        augmentMethods = {
            "set_status": set_status,
            "set_variable": set_variable,
        }
        super().execute(task, script, data, external_methods=augmentMethods)

    def eval(self, exp, data):
        return super()._eval(exp, {}, **data)


def show_form(task):
    form = task.task_spec.form

    if task.data is None:
        task.data = {}
    print(len(form.fields))
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
        return False


xx = CamundaParser()
xx.add_bpmn_file("./apps/workflow/top_workflow.bpmn")
xx.add_bpmn_file("./apps/workflow/common_workflow.bpmn")

spec = xx.get_spec("top_workflow")


if os.path.exists("ExampleSaveRestore.js"):
    f = open("ExampleSaveRestore.js")
    state = f.read()
    f.close()
    workflow = BpmnSerializer().deserialize_workflow(state, workflow_spec=None)
    # workflow = BpmnWorkflow(spec)
else:

    workflow = BpmnWorkflow(spec)


script_engine = BpmnScriptEngine(
    scriptingAdditions={
        "set_status": set_status,
        "set_variable": set_variable,
    }
)

workflow.script_engine = CustomBpmnScriptEngine()

# t = workflow.get_tasks()[1]
# t.update_data(
#     {
#         "initial_data": "my_data",
#     }
# )
# print(t)
# print(t.dump())
workflow.do_engine_steps()
ready_tasks = workflow.get_ready_user_tasks()

print(len(ready_tasks))
while len(ready_tasks) > 0:
    for task in ready_tasks:
        print(task.id)
        if isinstance(task.task_spec, UserTask):
            # print(task)
            # print(task.get_spec_data())
            # print(task.dump())
            # print(task.task_spec.name)
            # print(task.task_info())
            # print(task.data)
            show_form(task)
            print(task.data)
        else:
            print("Complete Task ", task.task_spec.name)
        workflow.complete_task_from_id(task.id)
        state = BpmnSerializer().serialize_workflow(workflow)
        f = open("ExampleSaveRestore.js", "w")
        f.write(state)
        f.close()
    workflow.do_engine_steps()
    ready_tasks = workflow.get_ready_user_tasks()
print("all tasks completed?")
print(workflow.last_task.data)
