from apps.summons.models import Summon, SummonedPerson, SummonType
from django.contrib import admin

admin.site.register(SummonType, admin.ModelAdmin)
admin.site.register(Summon, admin.ModelAdmin)
admin.site.register(SummonedPerson, admin.ModelAdmin)
