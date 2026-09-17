from apps.addresses.models import Address
from django.conf import settings
from django.db import models


class RuimteNaam(models.TextChoices):
    WOONKAMER = "woonkamer", "Woonkamer"
    KEUKEN = "keuken", "Keuken"
    SLAAPKAMER = "slaapkamer", "Slaapkamer"
    BADKAMER = "badkamer", "Badkamer"
    TOILETRUIMTE = "toiletruimte", "Toiletruimte"
    WASRUIMTE_BIJKEUKEN = "wasruimte_bijkeuken", "Wasruimte/bijkeuken"
    BERGING = "berging", "Berging"
    KELDER = "kelder", "Kelder"
    ZOLDER = "zolder", "Zolder"
    VERKEERSRUIMTE = "verkeersruimte", "Verkeersruimte"
    PRIVE_PARKEERRUIMTE = "prive_parkeerruimte", "Prive parkeerruimte"


def default_extra_ruimten():
    return []


class Kengetal(models.Model):
    badkamer_toilet_hangend_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=2.75
    )
    badkamer_toilet_normaal_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=2.00
    )
    badkamer_wastafel_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    badkamer_meerpersoons_wastafel_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.50
    )
    badkamer_douche_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=3.00
    )
    badkamer_bad_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=5.00
    )
    badkamer_baddouche_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=6.00
    )
    badkamer_bubbelfunctie_bad_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.50
    )
    badkamer_volledige_afscheiding_douche_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.25
    )
    badkamer_handdoekenradiator_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    badkamer_kast_bij_wastafel_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    badkamer_kastruimte_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    badkamer_stopcontacten_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.25
    )
    badkamer_stopcontacten_max = models.PositiveIntegerField(default=2)
    badkamer_eenhandsmengkraan_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.25
    )
    badkamer_thermostatische_mengkraan_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.50
    )
    keuken_aanrecht_grens_1 = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    keuken_aanrecht_grens_2 = models.DecimalField(
        max_digits=8, decimal_places=2, default=2.00
    )
    keuken_aanrecht_grens_3 = models.DecimalField(
        max_digits=8, decimal_places=2, default=3.00
    )
    keuken_aanrecht_grens_4 = models.DecimalField(
        max_digits=8, decimal_places=2, default=5.00
    )
    keuken_aanrecht_punten_1 = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00
    )
    keuken_aanrecht_punten_2 = models.DecimalField(
        max_digits=8, decimal_places=2, default=4.00
    )
    keuken_aanrecht_punten_3 = models.DecimalField(
        max_digits=8, decimal_places=2, default=7.00
    )
    keuken_aanrecht_punten_4 = models.DecimalField(
        max_digits=8, decimal_places=2, default=10.00
    )
    keuken_aanrecht_punten_5 = models.DecimalField(
        max_digits=8, decimal_places=2, default=13.00
    )
    keuken_inbouw_afzuiginstallatie_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    keuken_inbouw_kookplaat_inductie_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.75
    )
    keuken_inbouw_kookplaat_keramisch_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    keuken_inbouw_kookplaat_gas_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.50
    )
    keuken_inbouw_koelkast_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    keuken_inbouw_vrieskast_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    keuken_inbouw_oven_elektrisch_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    keuken_inbouw_oven_gas_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.50
    )
    keuken_inbouw_magnetron_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    keuken_inbouw_vaatwasmachine_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.50
    )
    keuken_extra_kastruimte_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    keuken_eenhandsmengkraan_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.25
    )
    keuken_thermostatische_mengkraan_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.50
    )
    keuken_kokendwaterfunctie_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.50
    )
    apart_toilet_staand_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=3.00
    )
    apart_toilet_hangend_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=3.75
    )
    vertrekken_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    overige_ruimte_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    verwarming_aantal_vertrekken_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=2.00
    )
    verwarming_aantal_overige_ruimten_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    verwarming_aantal_overige_ruimten_max = models.PositiveIntegerField(default=4)
    verkoeling_aantal_vertrekken_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    verkoeling_aantal_vertrekken_max = models.PositiveIntegerField(default=2)
    buitenruimte_prive_buitenruimte_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    buitenruimte_gemeenschappelijke_buitenruimte_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    buitenruimte_geen_gemeenschappelijke_aftrek = models.DecimalField(
        max_digits=8, decimal_places=2, default=5.00
    )
    parkeerruimte_gesloten_garage_bij_complex_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=9.00
    )
    parkeerruimte_buiten_bij_complex_met_dak_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=6.00
    )
    parkeerruimte_buiten_bij_complex_zonder_dak_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=4.00
    )
    bijzondere_voorziening_intercom_met_beeld_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    bijzondere_voorziening_laadpaal_factor = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    woz_kengetallen_per_peiljaar = models.JSONField(default=dict)
    woz_gemiddelde_regio_per_m2 = models.DecimalField(
        max_digits=8, decimal_places=2, default=7111.00
    )
    woz_percentage_grens = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00
    )
    woz_punten_boven_grens = models.DecimalField(
        max_digits=8, decimal_places=2, default=14.00
    )
    woz_punten_binnen_grens = models.DecimalField(
        max_digits=8, decimal_places=2, default=12.00
    )
    woz_punten_onder_grens = models.DecimalField(
        max_digits=8, decimal_places=2, default=10.00
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Kengetallen {self.id}"


class Gebruikersinvoer(models.Model):
    adres = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name="puntenteller_gebruikersinvoer",
    )
    gebruiker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="puntenteller_gebruikersinvoer",
    )
    completed = models.BooleanField(default=False)
    apart_toilet_staand = models.PositiveIntegerField(default=0)
    apart_toilet_hangend = models.PositiveIntegerField(default=0)
    vertrekken = models.JSONField(default=default_extra_ruimten, blank=True)
    overige_ruimten = models.JSONField(default=default_extra_ruimten, blank=True)
    verkeersruimten = models.JSONField(default=default_extra_ruimten, blank=True)
    buitenruimte_prive_buitenruimte = models.PositiveIntegerField(default=0)
    buitenruimte_gemeenschappelijke_buitenruimte = models.PositiveIntegerField(
        default=0
    )
    parkeerruimte_gesloten_garage_bij_complex = models.PositiveIntegerField(default=0)
    parkeerruimte_buiten_bij_complex_met_dak = models.PositiveIntegerField(default=0)
    parkeerruimte_buiten_bij_complex_zonder_dak = models.PositiveIntegerField(default=0)
    energielabel_klasse = models.CharField(max_length=10, null=True, blank=True)
    gebruiksoppervlakte = models.PositiveIntegerField(default=0)
    woz_waarde = models.PositiveIntegerField(default=0)
    woz_peildatum_jaar = models.PositiveIntegerField(default=2025)
    woz_kleine_nieuwbouwwoning = models.BooleanField(default=False)
    woz_nieuwbouw_2015_2019 = models.BooleanField(default=False)
    woz_bouwvoltooiingspercentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    monument = models.BooleanField(default=False)
    monument_soort = models.CharField(max_length=255, null=True, blank=True)
    bijzondere_voorziening_intercom_met_beeld = models.PositiveIntegerField(default=0)
    bijzondere_voorziening_laadpaal = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.adres} - {self.id}"
