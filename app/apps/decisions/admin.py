from apps.decisions.models import Decision, DecisionType
from django.contrib import admin

admin.site.register(Decision, admin.ModelAdmin)
admin.site.register(DecisionType, admin.ModelAdmin)
