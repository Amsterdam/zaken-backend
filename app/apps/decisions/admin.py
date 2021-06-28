from apps.decisions.models import Decision, DecisionType
from apps.decisions.serializers import DecisionSanctionSerializer
from django.contrib import admin
from django.http import JsonResponse


class DecisionAdmin(admin.ModelAdmin):
    actions = ["export_as_json"]

    def export_as_json(self, request, queryset):
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
