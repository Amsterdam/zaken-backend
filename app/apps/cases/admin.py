from apps.cases.models import Case, CaseState, CaseStateType
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "identification", "start_date", "end_date", "address")
