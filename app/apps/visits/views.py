from apps.users.auth_apps import TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import ViewSet

from .models import Visit
from .serializers import VisitSerializer


class VisitViewSet(ViewSet, CreateModelMixin):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()
