from apps.cases.models import Case
from apps.main.filters import RelatedOrderingFilter
from apps.main.pagination import EmptyPagination
from apps.users.auth_apps import TopKeyAuth
from apps.users.permissions import CanAccessSensitiveCases, IsInAuthorizedRealm
from django_filters import rest_framework as filters
from rest_framework import viewsets

from .serializers import DataTeamCaseSerializer


class StandardResultsSetPagination(EmptyPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class DataTeamCaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dedicated endpoint for data-team Wonen.
    """

    queryset = Case.objects.all()
    serializer_class = DataTeamCaseSerializer
    permission_classes = [(IsInAuthorizedRealm & CanAccessSensitiveCases) | TopKeyAuth]
    filter_backends = (
        filters.DjangoFilterBackend,
        RelatedOrderingFilter,
    )
    ordering_fields = "__all_related__"
    pagination_class = StandardResultsSetPagination
