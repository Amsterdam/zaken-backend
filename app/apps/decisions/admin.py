from apps.decisions.models import Decision, DecisionType
from apps.decisions.serializers import DecisionSanctionSerializer
from django.contrib import admin
from django.http import JsonResponse


class DecisionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "decision_type",
        "date_added",
        "sanction_id",
        "sanction_amount",
        "case_user_task_id",
    )
    list_filter = ("date_added",)
    date_hierarchy = "date_added"
    actions = ["export_decisions_with_sanction"]
    search_fields = ("case__id",)
    list_editable = ("decision_type",)

    def export_decisions_with_sanction(self, request, queryset):
        serializer = DecisionSanctionSerializer(
            queryset.filter(
                sanction_id__isnull=False,
                sanction_amount__isnull=False,
            ),
            many=True,
        )
        return JsonResponse({"decisions": serializer.data})


class DecisionTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "workflow_option",
        "is_sanction",
        "theme",
    )


admin.site.register(Decision, DecisionAdmin)
admin.site.register(DecisionType, DecisionTypeAdmin)
