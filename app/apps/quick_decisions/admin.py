from apps.quick_decisions.models import QuickDecision, QuickDecisionType
from django.contrib import admin


class QuickDecisionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "quick_decision_type",
        "date_added",
        "author",
        "case_user_task_id",
    )
    list_filter = ("date_added",)
    date_hierarchy = "date_added"
    search_fields = ("case__id",)
    list_editable = ("quick_decision_type",)


class QuickDecisionTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "workflow_option",
        "theme",
    )
    search_fields = (
        "name",
        "workflow_option",
    )
    list_filter = ("theme",)


admin.site.register(QuickDecision, QuickDecisionAdmin)
admin.site.register(QuickDecisionType, QuickDecisionTypeAdmin)
