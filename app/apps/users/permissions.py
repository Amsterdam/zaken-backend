from apps.cases.models import Case
from apps.users.auth_apps import TonKeyAuth, TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework.permissions import BasePermission

custom_permissions = [
    # Permissions for cases/tasks
    ("create_case", "Create a new Case"),
    ("create_digital_surveilance_case", "Create a new 'Digitaal toezicht' Case"),
    ("close_case", "Close a Case (by performing the last task)"),
    ("perform_task", "Can perform a tasks"),
    # Permissions to access remote API's
    (
        "access_personal_data_register",
        "Can access 'BRP' (persoonsgegevens / ingeschreven personen)",
    ),
    (
        "access_business_register",
        "Can access 'Handelsregister' (bedrijfseigenaren van panden, bedrijfsinformatie)",
    ),
    ("access_signals", "Can access 'SIA' (signalen)"),
    ("access_recovery_check", "Can access 'invorderingscheck'"),
    ("access_sensitive_dossiers", "Can read gevoelige dossiers"),
    ("access_sigital_surveillance", "Can read 'Digitaal toezicht'"),
    ("access_document_management_system", "Can access 'DMS' (Alfresco / Decos)"),
]


class CanAccessBRP(BasePermission):
    """
    Custom permission to only allow users with access_personal_data_register permissions
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.access_personal_data_register")


class CanCreateCase(BasePermission):
    """
    Custom permission to only allow users with create-case permissions
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.create_case")


class CanCreateDigitalSurveillanceCase(BasePermission):
    """
    Custom permission to only allow users with create-case permissions
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.create_digital_surveilance_case")


class CanPerformTask(BasePermission):
    """
    Custom permission to only allow users with perform-task permissions
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.perform_task")


class CanCloseCase(BasePermission):
    """
    Custom permission to only allow users with close-case permissions
    """

    def has_permission(self, request, view):
        return request.user.has_perm("users.close_case")


class CanAccessSensitiveCases(BasePermission):
    """
    Custom permission to only allow users with access_sensitive_dossiers permissions on sensitive cases
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):

        if issubclass(obj.__class__, Case) and not obj.sensitive:
            return True
        elif (
            hasattr(obj, "case")
            and hasattr(obj.case, "sensitive")
            and not obj.case.sensitive
        ):
            return True

        if request.user.has_perm("users.access_sensitive_dossiers"):
            return True

        return False


def rest_permission_classes_for_top():
    return [(IsInAuthorizedRealm) | TopKeyAuth]


def rest_permission_classes_for_ton():
    return [(IsInAuthorizedRealm) | TonKeyAuth]
