from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook

from .models import ScopedViewToken, User, UserGroup

admin.site.unregister(Group)


@admin.action(description="Assign 'BRP_GEGEVENS_INZIEN' role")
def assign_brp_gegevens_inzien(modeladmin, request, queryset):
    """
    Admin action to assign the 'BRP_GEGEVENS_INZIEN' role to selected users.
    """
    group, _ = UserGroup.objects.get_or_create(
        name="BRP_GEGEVENS_INZIEN", defaults={"display_name": "BRP gegevens inzien"}
    )
    processed_users = 0
    for user in queryset:
        if not user.groups.filter(id=group.id).exists():
            user.groups.add(group)
        processed_users += 1
    modeladmin.message_user(
        request,
        f"Assigned 'BRP_GEGEVENS_INZIEN' to {processed_users} selected user(s).",
    )


@admin.action(description="Geselecteerde gebruikers exporteren inclusief groepen")
def export_selected_users_to_excel(modeladmin, request, queryset):
    wb = Workbook()
    wb_sheet = wb.active
    wb_sheet.title = "Gebruikers inclusief groepen"

    headers = [
        "Naam",
        "E-mailadres",
        "Groepen",
        "Datum account aangemaakt",
        "Laatste login",
        "Actief",
    ]
    wb_sheet.append(headers)

    for u in queryset.prefetch_related("groups"):
        date_joined = (
            timezone.localtime(u.date_joined).strftime("%d-%m-%Y %H:%M:%S")
            if u.date_joined
            else ""
        )
        last_login = (
            timezone.localtime(u.last_login).strftime("%d-%m-%Y %H:%M:%S")
            if u.last_login
            else ""
        )
        full_name = f"{u.first_name} {u.last_name}".strip()
        wb_sheet.append(
            [
                full_name,
                u.email,
                ", ".join(g.name for g in u.groups.all()),
                date_joined,
                last_login,
                "Ja" if u.is_active else "Nee",
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="gebruikers_groepen.xlsx"'
    wb.save(response)
    return response


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
    actions = [assign_brp_gegevens_inzien, export_selected_users_to_excel]
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
    list_display = ("full_name", "email", "is_staff", "last_login", "date_joined")
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
