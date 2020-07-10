import logging

from django.conf import settings
from django.contrib.auth import get_user_model

LOGGER = logging.getLogger(__name__)

DEFAULT_EMAIL = "local.user@dev.com"
DEFAULT_USERNAME = "Local User"
DEFAULT_FIRST_NAME = "local"
DEFAULT_LAST_NAME = "user"


class DevelopmentAuthenticationBackend:
    def authenticate(self, request):
        assert settings.ENVIRONMENT not in [
            "production",
            "acceptance",
        ], "Development authenticate not allowed"
        assert settings.DEBUG, "Development authenticate only allowed in Debug mode"
        assert (
            settings.LOCAL_DEVELOPMENT_AUTHENTICATION
        ), "Local development authentication should be set to True"

        user_model = get_user_model()

        try:
            user = user_model.objects.get(email=DEFAULT_EMAIL)
        except user_model.DoesNotExist:
            user = user_model.objects.create_user(DEFAULT_EMAIL)

        user.first_name = DEFAULT_FIRST_NAME
        user.last_name = DEFAULT_LAST_NAME
        user.save()

        return user
