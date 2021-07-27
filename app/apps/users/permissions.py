from apps.users.auth_apps import CamundaKeyAuth, TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework.permissions import DjangoModelPermissions


class AppsDjangoModelPermissions(DjangoModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


def rest_permission_classes_for_top():
    return [(IsInAuthorizedRealm & AppsDjangoModelPermissions) | TopKeyAuth]


def rest_permission_classes_for_camunda():
    return [(IsInAuthorizedRealm & AppsDjangoModelPermissions) | CamundaKeyAuth]
