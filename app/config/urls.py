from apps.addresses.views import AddressViewSet
from apps.cases.views import (
    CaseCloseReasonViewSet,
    CaseCloseResultViewSet,
    CaseCloseViewSet,
    CaseDocumentViewSet,
    CaseStateViewSet,
    CaseThemeViewSet,
    CaseViewSet,
    CitizenReportViewSet,
    DocumentTypeViewSet,
    ImportBWVCaseDataView,
    download_data,
)
from apps.debriefings.views import DebriefingViewSet
from apps.decisions.views import DecisionTypeViewSet, DecisionViewSet
from apps.fines.views import FinesViewSet
from apps.gateway.push.views import PushViewSet
from apps.openzaak.views import ReceiveNotificationView
from apps.schedules.views import (
    ActionViewSet,
    DaySegmentViewSet,
    PriorityViewSet,
    ScheduleViewSet,
    WeekSegmentViewSet,
)
from apps.summons.views import SummonedPersonViewSet, SummonTypeViewSet, SummonViewSet
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
router.register(r"documents", CaseDocumentViewSet, basename="documents")
router.register(r"document-types", DocumentTypeViewSet, basename="document-types")
router.register(r"tasks", CaseUserTaskViewSet, basename="tasks")
router.register(r"themes", CaseThemeViewSet, basename="themes")
router.register(r"debriefings", DebriefingViewSet, basename="debriefings")
router.register(r"decisions", DecisionViewSet, basename="decisions")
router.register(r"decision-types", DecisionTypeViewSet, basename="decision-types")
router.register(r"push", PushViewSet, basename="push")
router.register(r"support-contacts", SupportContactView, basename="support-contact")
router.register(r"visits", VisitViewSet, basename="visits")
router.register(r"fines", FinesViewSet, basename="fines")
router.register(r"users", UserListView, basename="users")
router.register(r"permissions", PermissionViewSet, basename="permissions")
router.register(r"summons", SummonViewSet, basename="summons")
router.register(r"summon-types", SummonTypeViewSet, basename="summon-types")
router.register(r"summoned-persons", SummonedPersonViewSet, basename="summoned-persons")
router.register(r"schedules", ScheduleViewSet, basename="schedules")
router.register(r"schedule-actions", ActionViewSet, basename="schedule-actions")
router.register(
    r"schedule-weeksegments", WeekSegmentViewSet, basename="schedule-weeksegments"
)
router.register(
    r"schedule-daysegments", DaySegmentViewSet, basename="schedule-daysegments"
)
router.register(r"schedule-priorities", PriorityViewSet, basename="schedule-priorities")
router.register(r"case-close", CaseCloseViewSet, basename="case-closing")
router.register(r"case-states", CaseStateViewSet, basename="case-states")
router.register(
    r"case-close-results", CaseCloseResultViewSet, basename="case-close-results"
)
router.register(
    r"case-close-reasons", CaseCloseReasonViewSet, basename="case-close-reasons"
)
router.register(r"citizen-reports", CitizenReportViewSet, basename="citizen-reports")

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
