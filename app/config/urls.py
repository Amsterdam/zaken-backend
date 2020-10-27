from apps.cases.views import (
    AddressViewSet,
    CaseStateViewSet,
    CaseTimeLineReactionViewSet,
    CaseTimeLineThreadViewSet,
    CaseTimeLineViewSet,
    CaseTypeViewSet,
    CaseViewSet,
    PermitViewSet,
    TestEndPointViewSet,
)
from apps.debriefings.views import DebriefingViewSet
from apps.gateway.push.views import PushViewSet
from apps.users.views import IsAuthenticatedView, ObtainAuthTokenOIDC, UserListView
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"cases", CaseViewSet, basename="cases")
router.register(r"case-states", CaseStateViewSet, basename="cases-states")
router.register(r"case-timelines", CaseTimeLineViewSet, basename="case-timelines")
router.register(
    r"case-timeline-threads",
    CaseTimeLineThreadViewSet,
    basename="case-timeline-threads",
)
router.register(
    r"case-timeline-reactions",
    CaseTimeLineReactionViewSet,
    basename="case-timeline-reactions",
)
router.register(r"case-types", CaseTypeViewSet, basename="case-types")
router.register(r"addresses", AddressViewSet, basename="addresses")
router.register(r"push", PushViewSet, basename="push")
router.register(r"permits", PermitViewSet, basename="permits")
router.register(r"debriefings", DebriefingViewSet, basename="debriefings")
router.register(r"testing-url", TestEndPointViewSet, basename="testing-url")

urlpatterns = [
    # Admin environment
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
        "api/v1/is-authenticated/",
        IsAuthenticatedView.as_view(),
        name="is-authenticated",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON handlers for errors
handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
