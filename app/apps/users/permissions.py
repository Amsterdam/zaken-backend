from apps.users.auth_apps import CamundaKeyAuth, TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm


def rest_permission_classes_for_top():
    return [(IsInAuthorizedRealm) | TopKeyAuth]


def rest_permission_classes_for_camunda():
    return [(IsInAuthorizedRealm) | CamundaKeyAuth]
