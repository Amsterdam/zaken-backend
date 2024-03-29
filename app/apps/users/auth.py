import logging

from django.conf import settings
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from keycloak_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .auth_dev import DevelopmentAuthenticationBackend

LOGGER = logging.getLogger(__name__)


# TODO: email lowercase needs testing first
class AppsOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def get_userinfo(self, access_token, id_token, payload):
        user_info = super().get_userinfo(access_token, id_token, payload)

        # make sure email is lower case
        user_info["email"] = user_info.get("email", "").lower()

        return user_info

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified email."""
        email = claims.get("email")
        if not email:
            return self.UserModel.objects.none()

        users = self.UserModel.objects.filter(email__exact=email)
        return users


if settings.LOCAL_DEVELOPMENT_AUTHENTICATION:
    AuthenticationBackend = DevelopmentAuthenticationBackend
    AuthenticationClass = JWTAuthentication
else:
    AuthenticationBackend = OIDCAuthenticationBackend
    AuthenticationClass = OIDCAuthentication


class OIDCScheme(SimpleJWTScheme):
    target_class = "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    name = "Authenticate"
