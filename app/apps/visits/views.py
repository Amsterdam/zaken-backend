from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Visit
from .serializers import AddVisitSerializer, VisitSerializer


class VisitViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()

    @extend_schema(
        request=AddVisitSerializer,
        description="Add Visit from TOP",
    )
    @action(detail=False, methods=["post"])
    def create_visit_from_top(self, request):
        serializer = AddVisitSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            visit = Visit().create_from_top(serializer.data)
            if visit:
                response = Response(VisitSerializer(visit).data)
                return response
            raise ValidationError("Case does not exist")
