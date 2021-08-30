from apps.cases.models import Case
from django.conf import settings
from django.db import models
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.task import Task as SpiffWorkflowTask


class Workflow(models.Model):
    case = models.ForeignKey(
        to=Case,
        related_name="workflows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    serialized_workflow_state = models.JSONField(null=True)

    serializer = BpmnSerializer
    proccess_conf = settings.VAKANTIEVERHUUR_PROCCESSES

    def _get_strip_extensie(self, file_name):
        return file_name.split(".")[0]

    def get_serializer(self):
        return self.serializer()

    def get_workflow_spec(self, spec_file=None, sub_files=[]):
        x = CamundaParser()
        if spec_file and sub_files:
            for f in sub_files:
                x.add_bpmn_file(f)
            x.add_bpmn_file(spec_file)
            return x.get_spec(self._get_strip_extensie(spec_file))
        else:
            for f in Workflow.proccess_conf.get("main_proccess"):
                x.add_bpmn_file(f)
            return x.get_spec(Workflow.proccess_conf.get("proccess_files"))

    def _get_serialized_workflow_state(self):
        if self.serialized_workflow_state:
            return self.serialized_workflow_state

    def get_workflow(self, workflow_spec):
        if not self._get_serialized_workflow_state():
            return BpmnWorkflow(workflow_spec)

        return self.get_serializer().deserialize_workflow(
            self._get_serialized_workflow_state(), workflow_spec=None
        )

    def _workflow_do_engine_steps(self, wf):
        wf.do_engine_steps()
        return wf

    def update_data(self, task_name, wf, data):
        wf = self._workflow_do_engine_steps(wf)
        ready_tasks = wf.get_ready_user_tasks()

        tasks = [t for t in ready_tasks if t.task_spec.name == task_name]
        if not tasks or len(tasks) > 1:
            return
        task = tasks[0]
        task.update_data(data)
        print(task.data)
        print(task.internal_data)
        print(task.get_spec_data())
        print(wf.name)
        return wf, task

    def _serialize_workflow_state(self, wf):
        return self.get_serializer().serialize_workflow(wf)

    def _set_serialized_workflow_state(self, serialized_state):
        self.serialized_workflow_state = serialized_state

    def get_ready_task_names(self, wf):
        wf = self._workflow_do_engine_steps(wf)
        ready_tasks = wf.get_ready_user_tasks()
        return [t.task_spec.name for t in ready_tasks]

    def get_user_task_form(self, task_name, wf):
        wf = self._workflow_do_engine_steps(wf)
        ready_tasks = wf.get_ready_user_tasks()
        tasks = [t for t in ready_tasks if t.task_spec.name == task_name]
        if not tasks or len(tasks) > 1:
            return {}
        return self._task_form_to_python(tasks[0].task_spec.form)

    def _task_form_to_python(self, form):
        return {
            "form": {"key": form.key},
            "fields": [f.__dict__ for f in form.fields],
        }

    def create_user_task(self, wf):
        wf = self._workflow_do_engine_steps(wf)
        ready_tasks = self.get_ready_task_names(wf)

        for task in ready_tasks:
            try:
                task = Task.objects.create(
                    task_name=task,
                    case=self.case,
                    workflow=self,
                )
            except Exception as e:
                print(e)
                return False
        return task

    def complete_user_task(self, task_name, wf, data):
        wf, task = self.update_data(task_name, wf, data)

        wf.complete_task_from_id(task.id)

        state = self._serialize_workflow_state(wf)
        self._set_serialized_workflow_state(state)
        self.save()

        self.create_user_task(wf)

    def set_initial_data(self, data):
        spec = self.get_workflow_spec()
        wf = self.get_workflow(spec)
        tl = wf.get_tasks(SpiffWorkflowTask.READY)
        if tl:
            tl[0].update_data(data)
            state = self._serialize_workflow_state(wf)
            self._set_serialized_workflow_state(state)

    def __str__(self):
        return f"{self.id}, case: {self.case.id}"


class Task(models.Model):
    completed = models.BooleanField(
        default=False,
    )
    task_name = models.CharField(
        max_length=255,
    )
    created = models.DateTimeField(auto_now_add=True)
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

    class Meta:
        unique_together = [["task_name", "workflow"]]
