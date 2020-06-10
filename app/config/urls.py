from django.conf import settings
from django.conf.urls import url, include
from django.urls import path
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from api import views
# from api import mocking_views

router = DefaultRouter()
router.register(r'state-types', views.StateTypeViewSet, basename='state-type')

urlpatterns = [
    url(r'^', include(router.urls)),
    # url('all-data', mocking_views.display_data),
    # url('generate-data', mocking_views.generate_data),
    # url('generate-case', mocking_views.generate_case),
    # url('delete-data', mocking_views.delete_data),
    # url('object', mocking_views.object_detail),
    # url('health-check', mocking_views.health_check),

    # Swagger/OpenAPI documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON handlers for errors
handler500 = 'rest_framework.exceptions.server_error'
handler400 = 'rest_framework.exceptions.bad_request'