from apps.cases.models import CaseTheme
from apps.cases.serializers import (
    CaseCloseReasonSerializer,
    CaseCloseResultSerializer,
    CaseProjectSerializer,
    CaseReasonSerializer,
    CaseThemeSerializer,
    SubjectSerializer,
    TagSerializer,
)
from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import ViolationTypeSerializer
from apps.decisions.serializers import DecisionTypeSerializer
from apps.quick_decisions.serializers import QuickDecisionTypeSerializer
from apps.schedules.serializers import ThemeScheduleTypesSerializer
from apps.summons.serializers import SummonTypeSerializer
from apps.users.permissions import rest_permission_classes_for_top
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class CaseThemeViewSet(ListAPIView, viewsets.ViewSet):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseThemeSerializer
    queryset = CaseTheme.objects.all()

    @extend_schema(
        description="Gets the reasons associated with the requested theme",
        responses={status.HTTP_200_OK: CaseReasonSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="reasons",
        methods=["get"],
    )
    def reasons(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.reasons.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseReasonSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the SummonTypes associated with the given theme",
        responses={status.HTTP_200_OK: SummonTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="summon-types",
        methods=["get"],
    )
    def summon_types(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.summon_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = SummonTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the DecisionTypes associated with the given theme",
        responses={status.HTTP_200_OK: DecisionTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="decision-types",
        methods=["get"],
    )
    def decision_types(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.decision_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = DecisionTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the QuickDecisionTypes associated with the given theme",
        responses={status.HTTP_200_OK: QuickDecisionTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="quick-decision-types",
        methods=["get"],
    )
    def quick_decision_types(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.quick_decision_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = QuickDecisionTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the Scheduling Types associated with the given theme",
        responses={status.HTTP_200_OK: ThemeScheduleTypesSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="schedule-types",
        methods=["get"],
    )
    def schedule_types(self, request, pk):
        theme = self.get_object()
        serializer = ThemeScheduleTypesSerializer(theme)
        return Response(serializer.data)

    @extend_schema(
        description="Gets the ViolationTypes",
        responses={status.HTTP_200_OK: ViolationTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="violation-types",
        methods=["get"],
    )
    def violation_types(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        violation_choices = Debriefing.get_violation_choices_by_theme(theme.id)
        types = [{"key": key, "value": value} for key, value in violation_choices]
        context = paginator.paginate_queryset(types, request)
        serializer = ViolationTypeSerializer(context, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the CaseCloseReasons associated with the given theme",
        responses={status.HTTP_200_OK: CaseCloseReasonSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="case-close-reasons",
        methods=["get"],
    )
    def case_close_reasons(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.caseclosereason_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseCloseReasonSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the CaseProjects associated with the given theme",
        responses={status.HTTP_200_OK: CaseProjectSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="case-projects",
        methods=["get"],
    )
    def case_projects(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.caseproject_set.filter(
            active=True,
        )

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseProjectSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the CaseCloseResult associated with the given theme",
        responses={status.HTTP_200_OK: CaseCloseResultSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="case-close-results",
        methods=["get"],
    )
    def case_close_results(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.casecloseresult_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseCloseResultSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the subjects associated with the requested theme",
        responses={status.HTTP_200_OK: SubjectSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="subjects",
        methods=["get"],
    )
    def subjects(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.subject_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = SubjectSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the tags associated with the requested theme",
        responses={status.HTTP_200_OK: TagSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="tags",
        methods=["get"],
    )
    def tags(self, request, pk):
        paginator = LimitOffsetPagination()
        theme = self.get_object()
        query_set = theme.tag_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = TagSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)
