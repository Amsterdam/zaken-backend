from apps.cases.models import Address, Case, CaseType, State, StateType
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("identification", "start_date", "end_date", "case_type", "address")


@admin.register(CaseType)
class CaseTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ()


@admin.register(StateType)
class StateTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ()
