from apps.decisions.models import Decision, DecisionType
from apps.decisions.serializers import DecisionSanctionSerializer
from django.contrib import admin
from django.http import JsonResponse


class DecisionAdmin(admin.ModelAdmin):
    list_display = (
        "decision_type",
        "date_added",
        "sanction_id",
        "sanction_amount",
    )
    list_filter = ("date_added",)
    date_hierarchy = "date_added"
    actions = ["export_decisions_with_sanction"]

    def export_decisions_with_sanction(self, request, queryset):
        serializer = DecisionSanctionSerializer(
            queryset.filter(
                sanction_id__isnull=False,
                sanction_amount__isnull=False,
            ),
            many=True,
        )
        return JsonResponse({"decisions": serializer.data})


admin.site.register(Decision, DecisionAdmin)
admin.site.register(DecisionType, admin.ModelAdmin)
