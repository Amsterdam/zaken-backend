from django.conf import settings
from keycloak_oidc.drf.permissions import InAuthGroup


class IsInAuthorizedRealm(InAuthGroup):
    """
    A permission to allow access if and only if a user is logged in,
    and is a member of one of the OIDC_AUTHORIZED_GROUPS groups in Keycloak
    """

    assert settings.OIDC_AUTHORIZED_GROUPS, "OIDC_AUTHORIZED_GROUPS must be set"
    allowed_group_names = settings.OIDC_AUTHORIZED_GROUPS
