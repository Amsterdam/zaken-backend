from apps.users.auth_apps import TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
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
