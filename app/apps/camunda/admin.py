from apps.camunda.models import CamundaProcess, GenericCompletedTask
from django.contrib import admin


@admin.register(CamundaProcess)
class CamundaProcessOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "camunda_message_name",
        "to_directing_proccess",
        "theme",
    )


@admin.register(GenericCompletedTask)
class GenericCompletedTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "date_added",
        "description",
        "author",
    )
