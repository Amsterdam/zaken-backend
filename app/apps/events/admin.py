from apps.events.models import Event
from django.contrib import admin

admin.site.register(Event, admin.ModelAdmin, readonly_fields=("date_created", "values"))
