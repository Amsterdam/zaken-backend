from django.conf.urls import url

from app.api import views

urlpatterns = [
    url(r'^$', views.display_data),
    url('generate-data', views.generate_data),
    url('generate-case', views.generate_case),
    url('delete-data', views.delete_data),
    url('object', views.object_detail),
    url('health-check', views.health_check),

]
