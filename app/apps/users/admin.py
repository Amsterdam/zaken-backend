from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group

from .models import ScopedViewToken, User, UserGroup

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
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = ("id", "full_name", "email", "is_staff", "last_login", "date_joined")
    search_fields = ("email",)
    ordering = ("email",)
    readonly_fields = (
        "first_name",
        "last_name",
        "last_login",
        "date_joined",
        "username",
    )


@admin.register(ScopedViewToken)
class ScopedTokenAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "allowed_views")
    search_fields = ("user__username", "allowed_views")

    fields = ("key", "user", "allowed_views")
    readonly_fields = ("key",)
