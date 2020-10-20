from apps.cases.models import Case
from django_filters import rest_framework as filters


class CaseFilter(filters.FilterSet):
    state_date = filters.DateFilter(field_name="case_states__state_date", distinct=True)

    class Meta:
        model = Case
        fields = ["state_date"]
