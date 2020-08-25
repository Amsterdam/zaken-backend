from apps.cases.views import (
    AddressViewSet,
    CaseTimeLineReactionViewSet,
    CaseTimeLineThreadViewSet,
    CaseTimeLineViewSet,
    CaseTypeViewSet,
    CaseViewSet,
    GenerateMockViewset,
    PermitViewSet,
    StateTypeViewSet,
    StateViewSet,
)
from apps.gateway.push.views import PushCheckActionViewSet, PushViewSet
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
router.register(r"states", StateViewSet, basename="states")
router.register(r"state-types", StateTypeViewSet, basename="state-types")
router.register(r"generate-mock", GenerateMockViewset, basename="generate-mock")
router.register(r"push", PushViewSet, basename="push")
router.register(r"permits", PermitViewSet, basename="permits")
router.register(
    r"push-check-action", PushCheckActionViewSet, basename="push-check-action"
)

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
