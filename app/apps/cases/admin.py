from apps.cases.models import Address, Case, Project
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("identification", "start_date", "end_date", "project", "address")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ()
