import logging

from django.contrib.auth.models import Group
from django.db import transaction
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from mozilla_django_oidc import auth

CLAIMS_FIRST_NAME = "given_name"
CLAIMS_LAST_NAME = "family_name"
CLAIMS_ROLES = "roles"

LOGGER = logging.getLogger(__name__)


class OIDCScheme(SimpleJWTScheme):
    target_class = "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    name = "Authenticate"


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):
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

    # TODO: The roles aren't extracted properly yet
    def update_groups(self, user, claims):
        """
        Transform roles obtained from Grip into Django Groups and
        add them to the user. Note that any role not passed via Grip
        will be removed from the user.
        """
        with transaction.atomic():
            user.groups.clear()
            for role in claims.get(CLAIMS_ROLES, []):
                group, _ = Group.objects.get_or_create(name=role)
                group.user_set.add(user)
