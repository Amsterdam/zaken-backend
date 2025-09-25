import copy
import json

from django import forms

from .models import CaseWorkflow
from .spiff import compat as spiff_compat
from .tasks import task_update_workflow


class ResetSubworkflowsForm(forms.Form):
    subworkflow = forms.ChoiceField(
        widget=forms.RadioSelect(),
        choices=[[s, s] for s in CaseWorkflow.SUBWORKFLOWS],
    )

    def __init__(self, *args, **kwargs):
        kwargs.pop("caseworkflow", None)
        super().__init__(*args, **kwargs)

    field_order = ()

    def save(self, caseworkflow, test=True):
        subworkflow = self.data.get("subworkflow")
        result = caseworkflow.reset_subworkflow(subworkflow, test)
        return result


class UpdateDataForWorkflowsForm(forms.Form):
    json_data = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        kwargs.pop("caseworkflow", None)
        super().__init__(*args, **kwargs)

    field_order = ()

    def save(self, caseworkflow, test=True):
        json_data = self.data.get("json_data")
        result = {}
        data = {}
        try:
            data = json.loads(json_data)
        except Exception:
            result.update({"message": "Not a json string"})
            return result, False

        if not isinstance(data, dict) or not data:
            result.update({"message": "Not a dict or empty"})
            return result, False

        wf = caseworkflow.get_or_restore_workflow_state()
        current_data = {}
        if wf.last_task:
            current_data = copy.deepcopy(wf.last_task.data)

        data_to_be_changed = dict(
            (k, {"current": v, "new": data[k]})
            for k, v in current_data.items()
            if k in list(data.keys())
        )

        new_data = dict(
            (k, v) for k, v in data.items() if k not in list(current_data.keys())
        )
        result.update(
            {
                "message": "Valid",
                "data_to_be_changed": data_to_be_changed,
                "new_data": new_data,
            }
        )

        if not test:
            wf.last_task.update_data(data)
            for t in wf.last_task.children:
                t.update_data(data)
            serialize_wf = spiff_compat.serialize_workflow(wf, include_spec=False)
            caseworkflow.serialized_workflow_state = serialize_wf
            caseworkflow.save()
            task_update_workflow.delay(caseworkflow.id)

        return result, True
