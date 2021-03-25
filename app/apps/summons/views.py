import logging

from apps.summons.models import Summon, SummonType
from apps.summons.serializers import SummonSerializer, SummonTypeSerializer
from apps.users.auth_apps import TopKeyAuth
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class SummonViewSet(ViewSet, CreateModelMixin):
    serializer_class = SummonSerializer
    queryset = Summon.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case"]
