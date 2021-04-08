from apps.cases.models import Case
from apps.users.auth_apps import TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Visit
from .serializers import VisitSerializer


class VisitViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()

    def create(self, request):
        try:
            request.data.update(
                {"case": Case.objects.get(identification=request.data["case"]).id}
            )
        except Exception:
            # TODO Return valid response code if TOP task retry is fixed
            return Response({"Case not found"}, status=status.HTTP_202_ACCEPTED)
        return super().create(request)
