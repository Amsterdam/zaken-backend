import logging

from django.contrib.auth.models import Group
from django.db import transaction
from mozilla_django_oidc import auth

CLAIMS_FIRST_NAME = "given_name"
CLAIMS_LAST_NAME = "family_name"
CLAIMS_REALM_ACCESS = "realm_access"
CLAIMS_GROUPS = "roles"


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):
    def save_user(self, user, claims):
        user.first_name = claims.get(CLAIMS_FIRST_NAME, "")
        user.last_name = claims.get(CLAIMS_LAST_NAME, "")
        user.save()

        self.update_groups(user, claims)

        return user

    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        user = self.save_user(user, claims)
        return user

    def update_user(self, user, claims):
        user = self.save_user(user, claims)
        return user

    def clear_realm_access_groups(self, user):
        """
        Clears the user from the realm access groups
        """
        realm_access_groups = self.get_settings("OIDC_ALLOWED_REALM_ACCESS_GROUPS", [])
        for realm_access_group in realm_access_groups:
            group, _ = Group.objects.get_or_create(name=realm_access_group)
            group.user_set.remove(user)

    def update_groups(self, user, claims):
        """
        Transform roles obtained from keycloak into Django Groups and
        add them to the user. Note that any role not passed via keycloak
        will be removed from the user.
        """
        with transaction.atomic():
            self.clear_realm_access_groups(user)

            for claims_group in claims.get(CLAIMS_GROUPS):
                group, _ = Group.objects.get_or_create(name=claims_group)
                group.user_set.add(user)

    def get_groups(self, access_info):
        realm_access = access_info.get(CLAIMS_REALM_ACCESS, {})
        groups = realm_access.get(CLAIMS_GROUPS, [])
        return groups

    def get_nonce(self, payload):
        if self.get_settings("OIDC_USE_NONCE", True):
            return payload.get("nonce")

        return None

    def get_userinfo(self, access_token, id_token, payload):
        """
        Get user details from the access_token and id_token and return
        them in a dict.
        """
        user_info = super().get_userinfo(access_token, id_token, payload)
        nonce = self.get_nonce(payload)
        access_info = self.verify_token(access_token, nonce=nonce)
        groups = self.get_groups(access_info)
        user_info[CLAIMS_GROUPS] = groups

        return user_info
