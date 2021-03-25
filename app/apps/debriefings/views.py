import logging

from apps.cases.models import Case
from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import DebriefingCreateSerializer
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class DebriefingViewSet(ViewSet, CreateModelMixin):
    serializer_class = DebriefingCreateSerializer
    queryset = Debriefing.objects.all()
