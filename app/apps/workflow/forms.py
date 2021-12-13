from django import forms

from .models import CaseWorkflow


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
