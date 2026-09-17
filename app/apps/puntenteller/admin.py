from django.contrib import admin

from .models import Gebruikersinvoer, Kengetal


@admin.register(Kengetal)
class KengetalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "badkamer_toilet_hangend_factor",
        "keuken_inbouw_kookplaat_inductie_factor",
        "verwarming_aantal_vertrekken_factor",
    )


@admin.register(Gebruikersinvoer)
class GebruikersinvoerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "adres",
        "gebruiker",
        "completed",
        "energielabel_klasse",
        "woz_waarde",
        "woz_peildatum_jaar",
    )
    list_filter = (
        "completed",
        "monument",
        "energielabel_klasse",
        "woz_peildatum_jaar",
    )
    search_fields = (
        "adres__bag_id",
        "adres__street_name",
        "adres__postal_code",
        "gebruiker__email",
    )
