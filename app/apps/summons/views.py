import logging

from apps.summons.models import Summon, SummonType
from apps.summons.serializers import SummonSerializer, SummonTypeSerializer
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class SummonViewSet(
    GenericViewSet,
    mixins.CreateModelMixin,
):
    serializer_class = SummonSerializer
    queryset = Summon.objects.all()
