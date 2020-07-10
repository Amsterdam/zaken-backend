import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from mozilla_django_oidc import auth

CLAIMS_FIRST_NAME = "FirstName"
CLAIMS_LAST_NAME = "LastName"
PAYLOAD_NONCE = "nonce"
CLAIMS_ROLES = "roles"
ACCESS_INFO_REALM = "realm_access"

LOGGER = logging.getLogger(__name__)


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):
    def authenticate(self, request):
        """Authenticates a user based on the OIDC code flow."""
        if request and hasattr(request, "data") and request.data.get("code", False):
            self.request = request
            code = self.request.data.get("code")
        else:
            return None

        """ Retrieve the redirect uri from the request """
        token_payload = {
            "client_id": self.OIDC_RP_CLIENT_ID,
            "client_secret": self.OIDC_RP_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.OIDC_REDIRECT_URL,
        }

        # Get the token
        token_info = self.get_token(token_payload)
        id_token = token_info.get("id_token")
        access_token = token_info.get("access_token")

        # Validate the token
        try:
            payload = self.verify_token(id_token)

            if payload:
                self.store_tokens(access_token, id_token)
                return self.get_or_create_user(access_token, id_token, payload)

        except SuspiciousOperation as exc:
            LOGGER.warning("failed authenticate and to get or create user: %s", exc)

        return None

    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)

        user.first_name = claims.get(CLAIMS_FIRST_NAME, "")
        user.last_name = claims.get(CLAIMS_LAST_NAME, "")
        user.save()

        self.update_groups(user, claims)
        return user

    def update_user(self, user, claims):
        user.first_name = claims.get(CLAIMS_FIRST_NAME, "")
        user.last_name = claims.get(CLAIMS_LAST_NAME, "")
        user.save()

        self.update_groups(user, claims)

        return user

    def update_groups(self, user, claims):
        """
        Transform roles obtained from Grip into Django Groups and
        add them to the user. Note that any role not passed via Grip
        will be removed from the user.
        """
        with transaction.atomic():
            user.groups.clear()
            for role in claims.get(CLAIMS_ROLES):
                group, _ = Group.objects.get_or_create(name=role)
                group.user_set.add(user)

    def get_userinfo(self, access_token, id_token, payload):
        """
        Get user details from the access_token and id_token and return
        them in a dict.
        """
        user_info = super().get_userinfo(access_token, id_token, payload)
        access_info = self.verify_token(access_token)
        roles = access_info.get(ACCESS_INFO_REALM, {}).get(CLAIMS_ROLES, [])

        user_info[CLAIMS_ROLES] = roles

        """
        NOTE: This is a temporary patch to support the capitalized user info email,
        instead of the lower capital email which is supposed to be retrieved using the
        (not yet supported) email scope.
        """
        user_info["email"] = user_info.get("Email")

        return user_info
