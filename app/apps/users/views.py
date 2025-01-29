import logging

from apps.users.permissions import IsInAuthorizedRealm
from django.contrib.auth.models import Permission
from django.http import HttpResponseBadRequest
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .auth import AuthenticationBackend
from .models import User
from .serializers import (
    IsAuthorizedSerializer,
    OIDCAuthenticateSerializer,
    UserDetailSerializer,
    UserSerializer,
)

LOGGER = logging.getLogger(__name__)


class UserListView(ViewSet, generics.ListAPIView):
    queryset = User.objects.filter(is_staff=False, is_active=True, is_superuser=False)
    serializer_class = UserSerializer

    @extend_schema(
        description="Gets the user data of you, as logged-in user",
        responses={status.HTTP_200_OK: UserDetailSerializer()},
    )
    @action(
        detail=False,
        url_path="me",
        methods=["get"],
    )
    def me(self, request):

        serializer = UserDetailSerializer(request.user)

        return Response(serializer.data)


class PermissionViewSet(ViewSet):
    queryset = Permission.objects.all()
    serializer_class = serializers.ListSerializer(child=serializers.CharField())

    @extend_schema(
        description="Gets all permissions",
        responses={200: serializers.ListSerializer(child=serializers.CharField())},
    )
    def list(self, request):
        return Response(self.queryset.values_list("codename", flat=True))


class IsAuthorizedView(APIView):
    permission_classes = ()
    serializer_class = IsAuthorizedSerializer

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
