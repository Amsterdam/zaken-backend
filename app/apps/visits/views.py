from apps.users.auth_apps import TopKeyAuth
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Visit
from .serializers import TopVisitSerializer, VisitSerializer


class VisitViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated | TopKeyAuth]
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()

    @extend_schema(
        request=TopVisitSerializer,
        description="Add Visit from TOP",
    )
    @action(detail=False, methods=["post"])
    def create_visit_from_top(self, request):
        serializer = TopVisitSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            visit = Visit().create_from_top(serializer.data)
            if visit:
                response = Response(VisitSerializer(visit).data)
                return response
            raise ValidationError("Case does not exist")

    @extend_schema(
        request=TopVisitSerializer,
        description="Update Visit from TOP",
    )
    @action(detail=False, methods=["post"])
    def update_visit_from_top(self, request):
        serializer = TopVisitSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            try:
                visit = Visit.objects.get(
                    case__identification=serializer.data["case_identification"],
                    start_time=serializer.data["start_time"],
                )
                visit = visit.update_from_top(serializer.data)
            except Visit.DoesNotExist:
                visit = Visit().create_from_top(serializer.data)

            if visit:
                visit.save()
                response = Response(VisitSerializer(visit).data)
                return response
            raise ValidationError("Case does not exist")
