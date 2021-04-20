from apps.camunda.models import CamundaProcess, GenericCompletedTask
from django.contrib import admin

admin.site.register(GenericCompletedTask)
admin.site.register(CamundaProcess)
