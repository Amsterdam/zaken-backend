from apps.users.auth_apps import TopKeyAuth
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Visit
from .serializers import VisitSerializer


class VisitViewSet(ModelViewSet):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()

    def create(self, request):
        print(request.data)
        return super().create(request)
