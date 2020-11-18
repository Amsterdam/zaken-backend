from apps.addresses.views import AddressViewSet
from apps.cases.views import CaseViewSet, TestEndPointViewSet
from apps.debriefings.views import DebriefingViewSet
from apps.gateway.push.views import PushViewSet
from apps.users.views import IsAuthorizedView, ObtainAuthTokenOIDC, UserListView
from apps.permits.views import PermitViewSet
from apps.visits.views import VisitViewSet
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"cases", CaseViewSet, basename="cases")
router.register(r"addresses", AddressViewSet, basename="addresses")
router.register(r"push", PushViewSet, basename="push")
router.register(r"debriefings", DebriefingViewSet, basename="debriefings")
router.register(r"visits", VisitViewSet, basename="visits")
# router.register(r"testing-url", TestEndPointViewSet, basename="testing-url")
router.register(r"test-permits", PermitViewSet, basename="test-permits")

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
        "api/v1/is-authorized/",
        IsAuthorizedView.as_view(),
        name="is-authorized",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON handlers for errors
handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
