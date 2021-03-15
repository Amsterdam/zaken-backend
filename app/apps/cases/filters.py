from apps.cases.models import Case
from django_filters import rest_framework as filters


class CaseFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="start_date")
    open_cases = filters.BooleanFilter(field_name="end_date", lookup_expr="isnull")
    team = filters.CharFilter(field_name="team__name", distinct=True)
    reason = filters.CharFilter(field_name="reason__name", distinct=True)
    status = filters.CharFilter(method="state_filter", distinct=True)

    class Meta:
        model = Case
        fields = ["start_date", "open_cases", "team", "reason", "status"]

    def state_filter(self, queryset, name, value):
        return queryset.filter(
            case_states__end_date__isnull=True, case_states__status__name=value
        )
