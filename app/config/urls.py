from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from api.mocking_views import GenerateMockViewset
from api.open_zaak.case.views import CaseViewSet
from api.open_zaak.case_object.views import CaseObjectViewSet
from api.open_zaak.case_type.views import CaseTypeViewSet
from api.open_zaak.catalog.views import CatalogViewSet
from api.open_zaak.state.views import StateViewSet
from api.open_zaak.state_type.views import StateTypeViewSet

router = DefaultRouter()
router.register(r'cases', CaseViewSet, basename='cases')
router.register(r'case-objects', CaseObjectViewSet, basename='case-objects')
router.register(r'case-types', CaseTypeViewSet, basename='case-types')
router.register(r'catalogs', CatalogViewSet, basename='catalogs')
router.register(r'states', StateViewSet, basename='states')
router.register(r'state-types', StateTypeViewSet, basename='state-type')
router.register(r'generate-mock', GenerateMockViewset, basename='generate-mock')

urlpatterns = [
                  url(r'^', include(router.urls)),
                  path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
                  path('api/v1/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON handlers for errors
handler500 = 'rest_framework.exceptions.server_error'
handler400 = 'rest_framework.exceptions.bad_request'
