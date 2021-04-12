from apps.users.auth_apps import TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet

from .models import Visit
from .serializers import VisitSerializer


class VisitViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()

    def create(self, request):
        print(request.data)
        return super().create(request)
