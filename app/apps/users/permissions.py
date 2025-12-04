from apps.cases.models import Case
from apps.users.auth_apps import TonKeyAuth, TopKeyAuth
from django.conf import settings
from rest_framework.permissions import BasePermission, IsAuthenticated


class InAuthGroup(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsInAuthorizedRealm(InAuthGroup):
    """
    A permission to allow access if and only if a user is logged in,
    and is a member of one of the OIDC_AUTHORIZED_GROUPS groups in Keycloak
    """


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
        # Super users should not be allowed to access BRP in production
        if request.user.is_superuser and settings.ENVIRONMENT == "production":
            return False
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
        # Check if the user is authenticated using IsAuthenticated permission.
        return IsAuthenticated().has_permission(request, view)

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


class ScopedViewPermission(BasePermission):
    """
    Custom permission to only allow tokens for specific views / endpoints
    """

    def has_permission(self, request, view):
        token = getattr(request, "auth", None)
        if not token or not hasattr(token, "allowed_views"):
            return False
        allowed = [v.strip() for v in token.allowed_views.split(",") if v.strip()]
        return view.action in allowed
