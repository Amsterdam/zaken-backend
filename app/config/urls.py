from apps.addresses.views import AddressViewSet
from apps.cases.views import (
    CaseCloseViewSet,
    CaseThemeViewSet,
    CaseViewSet,
    ImportBWVCaseDataView,
    download_data,
)
from apps.debriefings.views import DebriefingViewSet
from apps.decisions.views import DecisionViewSet
from apps.fines.views import FinesViewSet
from apps.gateway.push.views import PushViewSet
from apps.openzaak.views import ReceiveNotificationView
from apps.schedules.views import ScheduleViewSet
from apps.summons.views import SummonViewSet
from apps.support.views import SupportContactView
from apps.users.views import (
    IsAuthorizedView,
    ObtainAuthTokenOIDC,
    PermissionViewSet,
    UserListView,
)
from apps.visits.views import VisitViewSet
from apps.workflow.views import CaseUserTaskViewSet, GenericCompletedTaskViewSet
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="addresses")
router.register(r"cases", CaseViewSet, basename="cases")
router.register(r"tasks", CaseUserTaskViewSet, basename="tasks")
router.register(r"themes", CaseThemeViewSet, basename="themes")
router.register(r"debriefings", DebriefingViewSet, basename="debriefings")
router.register(r"decisions", DecisionViewSet, basename="decisions")
router.register(r"push", PushViewSet, basename="push")
router.register(r"support-contacts", SupportContactView, basename="support-contact")
router.register(r"visits", VisitViewSet, basename="visits")
router.register(r"fines", FinesViewSet, basename="fines")
router.register(r"users", UserListView, basename="users")
router.register(r"permissions", PermissionViewSet, basename="permissions")
router.register(r"summons", SummonViewSet, basename="summons")
router.register(r"schedules", ScheduleViewSet, basename="schedules")
router.register(r"case-close", CaseCloseViewSet, basename="case-closing")

router.register(r"generic-tasks", GenericCompletedTaskViewSet, basename="generic-tasks")

urlpatterns = [
    # Admin environment
    path("admin/download_data/", download_data),
    path(
        "admin/import-bwv-cases",
        ImportBWVCaseDataView.as_view(),
        name="import-bwv-cases",
    ),
    path("admin/", admin.site.urls),
    # API Routing
    path("api/v1/", include(router.urls)),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Authentication endpoint for exchanging an OIDC code for a token
    path(
        "api/v1/oidc-authenticate/",
        ObtainAuthTokenOIDC.as_view(),
        name="oidc-authenticate",
    ),
    # Endpoint for checking if user is authenticated
    path(
        "api/v1/is-authorized/",
        IsAuthorizedView.as_view(),
        name="is-authorized",
    ),
    # Endpoint to receive the notification
    path(
        "api/v1/openzaak/callbacks",
        ReceiveNotificationView.as_view(),
        name="notification-callback",
    ),
    path("data-model/", include("django_spaghetti.urls")),
    url("health/", include("health_check.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON handlers for errors
handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
