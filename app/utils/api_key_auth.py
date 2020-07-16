from django.conf import settings
from rest_framework.permissions import BasePermission


class ApiKeyAuth(BasePermission):
    def has_permission(self, request, view):
        api_key_secret = request.META.get("HTTP_AUTHORIZATION", None)
        api_key_secret = api_key_secret.split("Bearer ")[-1]

        if api_key_secret:
            return api_key_secret in settings.SECRET_KEY_ACCESS

        return False
