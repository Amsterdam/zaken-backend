import logging

from apps.summons.models import Summon, SummonType
from apps.summons.serializers import SummonSerializer, SummonTypeSerializer
from apps.users.auth_apps import TopKeyAuth
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class SummonViewSet(ModelViewSet):
    serializer_class = SummonSerializer
    queryset = Summon.objects.all()
