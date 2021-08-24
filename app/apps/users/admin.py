from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group

from .models import User, UserGroup

admin.site.unregister(Group)


@admin.register(UserGroup)
class UserGroupAdmin(GroupAdmin):
    fields = (
        "name",
        "display_name",
        "permissions",
    )
    list_display = (
        "name",
        "display_name",
    )


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (
            "None",
            {"fields": ("email", "password", "username", "first_name", "last_name")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = ("full_name", "email", "is_staff")
    search_fields = ("email",)
    ordering = ("email",)
