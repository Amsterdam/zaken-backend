import os
from time import sleep

from SpiffWorkflow.bpmn.BpmnScriptEngine import BpmnScriptEngine
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import EnumFormField
from SpiffWorkflow.task import Task

x = CamundaParser()
x.add_bpmn_file("../../aza_wonen_global_afronden_zaak.bpmn")
x.add_bpmn_file("../../aza_wonen_global_voornemen_afzien.bpmn")
x.add_bpmn_file("../../aza_wonen_global_decision.bpmn")
x.add_bpmn_file("../../aza_wonen_global_summon.bpmn")
x.add_bpmn_file("../../aza_wonen_global_visit.bpmn")
x.add_bpmn_file("../../aza_wonen_local_vakantieverhuur_regie.bpmn")
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


def get_formfield_ids(task):
    form = task.task_spec.form

    return [field.id for field in form.fields]


xx = CamundaParser()
xx.add_bpmn_file("./top_workflow.bpmn")
xx.add_bpmn_file("./common_workflow.bpmn")

xxx = CamundaParser()
xxx.add_bpmn_file("./paralell_user_tasks.bpmn")

xxxx = CamundaParser()
xxxx.add_bpmn_file("./test_replay_by_data.bpmn")

spec = s  # xxxx.get_spec("test_replay_by_data")

# data = {"done": {"value": "Gedaan?"}, "names": {"value": "donald duck"}, "summon": {"value": "Yes"}, "situation": {"value": "access_granted"}, "summon_id": {"value": 96}, "violation": {"value": "YES"}, "status_name": "Huisbezoek", "opstellen_done": {"value": "jhgfytfhg"}, "type_aanschrijving": {"value": "aanschrijvingen"}, "can_next_visit_go_ahead": {"value": None}, "default_usertask_formfield": {"value": "yes"}, "opstellen_concept_aanschrijvingen_done": {"value": True}}
# data = {"status_name": "Huisbezoek"}
data = {
    "done": {"value": "Gedaan?"},
    "names": {"value": "donald duck"},
    "summon": {"value": "Yes"},
    "next_step": {"value": "decision"},
    "situation": {"value": "access_granted"},
    "summon_id": {"value": 99},
    "violation": {"value": "YES"},
    "status_name": "Huisbezoek",
    "type_besluit": {"value": "boete"},
    "opstellen_done": {"value": "jnghj"},
    "FormField_19ujdh2": {"value": True},
    "FormField_3113shb": {"value": True},
    "type_aanschrijving": {"value": "aanschrijvingen"},
    "timer_boundry_duration": "test",
    "can_next_visit_go_ahead": {"value": None},
    "default_usertask_formfield": {"value": "yes"},
    "is_citizen_objection_valid": {"value": "no_citizen_objection_not_valid"},
    "is_civilian_objection_received": {"value": "yes_objection_received"},
    "opstellen_concept_aanschrijvingen_done": {"value": True},
}

result_ready_tasks = ["Activity_14kdv7u", "Gateway_0f59geq", "Activity_1tl73nx"]
# result_ready_tasks = ["Activity_14kdv7u", "Activity_1tl73nx"]
found_ready_tasks = []

if os.path.exists("ExampleSaveRestore.js"):
    f = open("ExampleSaveRestore.js")
    state = f.read()
    f.close()
    # workflow = BpmnSerializer().deserialize_workflow(state, workflow_spec=spec)
    workflow = BpmnWorkflow(spec)
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
first_task = workflow.get_tasks(Task.READY)[0]
first_task.update_data(data)
# all_data = {'create_case_formfield': 'NEW MORE', 'some_test': 'some test val', 'test_field': 'STRANGE VAL', 'first_name': 'MOORTJE'}
workflow.do_engine_steps()
# task = workflow.get_task_spec_from_name("create_case")
# first_task.update_data({"create_case_formfield": "MORE"})
# task = workflow.get_ready_user_tasks()[0]
# first_task.data['collection'] = [1,2,3,4,5]
# workflow.complete_task_from_id(first_task.id)
ready_tasks = workflow.get_ready_user_tasks()
# print(workflow.get_tasks())
# for t in workflow.get_tasks():
# print(f"{t.task_spec.name} == {t.get_state_name()} == {t.last_state_change}")
task_mask = Task.READY | Task.WAITING


def get_tasks(wf):
    return wf.get_tasks(task_mask)


ready_tasks = get_tasks(workflow)

while len(ready_tasks) > 0:
    for task in ready_tasks:
        print(task.task_spec.name)

        if task.task_spec.name not in result_ready_tasks:
            task.update_data(data)
            workflow.complete_task_from_id(task.id)
        else:
            found_ready_tasks.append(task.task_spec.name)
        if sorted(found_ready_tasks) == sorted(result_ready_tasks):
            print("STOP")
            ready_tasks = []
            print(workflow.get_tasks(task_mask))
            print(workflow.get_tasks(Task.WAITING))
            break
        else:
            workflow.do_engine_steps()
            ready_tasks = get_tasks(workflow)

        # if isinstance(task.task_spec, UserTask):

        #     formfield_ids = sorted(get_formfield_ids(task))
        #     data_keys = list(data.keys())
        #     intersection = sorted([i for i in formfield_ids if i in data_keys])

        #     if intersection == formfield_ids:
        #         # print(task.task_spec.name)
        #         task.update_data(data)
        #         workflow.complete_task_from_id(task.id)
        #     else:
        #         event_task = workflow.get_tasks_from_spec_name("Event_0kmw6bf")
        #         print(event_task[0].get_state_name())
        #         print(event_task[0].task_spec.__dict__.get("event_definition").__dict__)
        #         print("complete timer")
        #         workflow.complete_task_from_id(event_task[0].id)
        #         workflow.do_engine_steps()
        #         workflow.complete_task_from_id(task.id)
        #         break

        # else:
        #     workflow.complete_task_from_id(task.id)
        #     print("Complete Task ", task.task_spec.name)

        sleep(0.1)

        # workflow.refresh_waiting_tasks()
        # state = BpmnSerializer().serialize_workflow(workflow,  include_spec=False)
        # f = open("ExampleSaveRestore.js", "w")
        # f.write(state)
        # f.close()
    # workflow.refresh_waiting_tasks()
    # workflow.do_engine_steps()

print("last task completed?")
print(ready_tasks)
