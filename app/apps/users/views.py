import logging

from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .auth import AuthenticationBackend
from .models import User
from .serializers import OIDCAuthenticateSerializer, UserSerializer

LOGGER = logging.getLogger(__name__)


class UserListView(ViewSet, generics.ListAPIView):
    permission_classes = ()
    queryset = User.objects.filter(is_staff=False, is_active=True, is_superuser=False)
    serializer_class = UserSerializer


class IsAuthorizedView(APIView):
    permission_classes = ()

    def get(self, request):
        is_authorized = IsInAuthorizedRealm().has_permission(request, self)
        return Response({"is_authorized": is_authorized})


class ObtainAuthTokenOIDC(APIView):
    serializer_class = OIDCAuthenticateSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        code = request.data.get("code", None)

        if not code:
            LOGGER.error("Could not authenticate: No authentication code found")
            return HttpResponseBadRequest("No authentication code found")

        authentication_backend = AuthenticationBackend()

        try:
            user = authentication_backend.authenticate(request)
        except Exception as e:
            LOGGER.error("Could not authenticate: {}".format(str(e)))
            return HttpResponseBadRequest("Could not authenticate")

        try:
            refresh = RefreshToken.for_user(user)
        except Exception as e:
            LOGGER.error("Could not refresh token: {}".format(str(e)))
            return HttpResponseBadRequest("Could not refresh token")

        serialized_user = UserSerializer(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": serialized_user.data,
            }
        )


obtain_auth_token = ObtainAuthTokenOIDC.as_view()
