import logging

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from mozilla_django_oidc import auth

CLAIMS_FIRST_NAME = "given_name"
CLAIMS_LAST_NAME = "family_name"
CLAIMS_REALM_ACCESS = "realm_access"
CLAIMS_ROLES = "roles"

LOGGER = logging.getLogger(__name__)


class OIDCScheme(SimpleJWTScheme):
    target_class = "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    name = "Authenticate"


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):
    def save_user(self, user, claims):
        user.first_name = claims.get(CLAIMS_FIRST_NAME, "")
        user.last_name = claims.get(CLAIMS_LAST_NAME, "")
        user.save()
        return user

    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        user = self.save_user(user, claims)
        return user

    def update_user(self, user, claims):
        user = self.save_user(user, claims)
        return user

    def get_roles(self, access_info):
        realm_access = access_info.get(CLAIMS_REALM_ACCESS, {})
        roles = realm_access.get(CLAIMS_ROLES, [])
        return roles

    def verify_roles(self, roles):
        """
        Verify if the given roles are in the allowed roles settings
        """
        allowed_roles = settings.OIDC_ALLOWED_REALM_ACCESS_ROLES
        intersection = set(roles) & set(allowed_roles)

        if len(intersection) == 0:
            raise SuspiciousOperation(
                "The user is not authorized to access this application."
            )

    def get_userinfo(self, access_token, id_token, payload):
        """
        Return the retrieved user info if the access token and roles are verified
        """
        user_info = super().get_userinfo(access_token, id_token, payload)
        access_info = self.verify_token(access_token, nonce=None)

        roles = self.get_roles(access_info)
        self.verify_roles(roles)

        return user_info
