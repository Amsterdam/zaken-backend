from django.conf import settings
from rest_framework.permissions import BasePermission


class AppsKeyAuth(BasePermission):
    SECRET_KEY = None

    def has_permission(self, request, view):
        try:
            assert self.SECRET_KEY, "SECRET_KEY is not set"

            secret_key_request = request.META.get("HTTP_AUTHORIZATION", None)
            assert secret_key_request, "Secret key cannot be retrieved from request"

            has_permission = secret_key_request == self.SECRET_KEY

            return has_permission
        except AssertionError:
            return False


class TopKeyAuth(AppsKeyAuth):
    SECRET_KEY = settings.SECRET_KEY_TOP_ZAKEN
