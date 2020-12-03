from django.contrib import admin

from .models import SupportContact

admin.site.register(SupportContact, admin.ModelAdmin)
