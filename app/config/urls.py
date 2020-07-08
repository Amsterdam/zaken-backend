from apps.gateway.push.views import PushCheckActionViewSet, PushViewSet
from apps.open_zaak.case.views import CaseViewSet
from apps.open_zaak.case_object.views import CaseObjectViewSet
from apps.open_zaak.case_type.views import CaseTypeViewSet
from apps.open_zaak.catalog.views import CatalogViewSet
from apps.open_zaak.mocking_views import GenerateMockViewset
from apps.open_zaak.state.views import StateViewSet
from apps.open_zaak.state_type.views import StateTypeViewSet
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"cases", CaseViewSet, basename="cases")
router.register(r"case-objects", CaseObjectViewSet, basename="case-objects")
router.register(r"case-types", CaseTypeViewSet, basename="case-types")
router.register(r"catalogs", CatalogViewSet, basename="catalogs")
router.register(r"states", StateViewSet, basename="states")
router.register(r"state-types", StateTypeViewSet, basename="state-type")
router.register(r"generate-mock", GenerateMockViewset, basename="generate-mock")
router.register(r"push", PushViewSet, basename="push")
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON handlers for errors
handler500 = "rest_framework.exceptions.server_error"
handler400 = "rest_framework.exceptions.bad_request"
