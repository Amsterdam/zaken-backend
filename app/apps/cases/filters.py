from apps.cases.models import Case
from django_filters import rest_framework as filters


class CaseFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="case_states__start_date", distinct=True)

    class Meta:
        model = Case
        fields = ["start_date"]
