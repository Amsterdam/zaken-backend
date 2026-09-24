from apps.addresses.models import Address
from django.conf import settings
from django.db import models


class RuimteNaam(models.TextChoices):
    WOONKAMER = "woonkamer", "Woonkamer"
    KEUKEN = "keuken", "Keuken"
    SLAAPKAMER = "slaapkamer", "Slaapkamer"
    BADKAMER = "badkamer", "Badkamer"
    TOILETRUIMTE = "toiletruimte", "Toiletruimte"
    PRIVE_BUITENRUIMTE = "prive_buitenruimte", "Prive buitenruimte"
    GEMEENSCHAPPELIJKE_BUITENRUIMTE = (
        "gemeenschappelijke_buitenruimte",
        "Gemeenschappelijke buitenruimte",
    )
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
        max_digits=8, decimal_places=2, default=2.00
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
    woonvoorziening_handicap_bedrag_per_punt = models.DecimalField(
        max_digits=8, decimal_places=2, default=332.00
    )
    sanitair_wastafel_niet_badkamer_max_punten = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.00
    )
    sanitair_meerpersoons_wastafel_niet_badkamer_max_punten = models.DecimalField(
        max_digits=8, decimal_places=2, default=1.50
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
    buitenruimte_prive_basispunten = models.DecimalField(
        max_digits=8, decimal_places=2, default=2.00
    )
    buitenruimte_prive_punten_per_m2 = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.35
    )
    buitenruimte_gemeenschappelijke_punten_per_m2 = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.75
    )
    buitenruimte_max_punten = models.DecimalField(
        max_digits=8, decimal_places=2, default=15.00
    )
    buitenruimte_geen_buitenruimte_aftrek = models.DecimalField(
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
    energieprestatie_label_a4plus_eengezinswoning_punten = models.SmallIntegerField(
        default=62
    )
    energieprestatie_label_a4plus_meergezinswoning_punten = models.SmallIntegerField(
        default=58
    )
    energieprestatie_label_a3plus_eengezinswoning_punten = models.SmallIntegerField(
        default=57
    )
    energieprestatie_label_a3plus_meergezinswoning_punten = models.SmallIntegerField(
        default=53
    )
    energieprestatie_label_a2plus_eengezinswoning_punten = models.SmallIntegerField(
        default=52
    )
    energieprestatie_label_a2plus_meergezinswoning_punten = models.SmallIntegerField(
        default=48
    )
    energieprestatie_label_aplus_eengezinswoning_punten = models.SmallIntegerField(
        default=47
    )
    energieprestatie_label_aplus_meergezinswoning_punten = models.SmallIntegerField(
        default=43
    )
    energieprestatie_label_a_eengezinswoning_punten = models.SmallIntegerField(
        default=41
    )
    energieprestatie_label_a_meergezinswoning_punten = models.SmallIntegerField(
        default=37
    )
    energieprestatie_label_b_eengezinswoning_punten = models.SmallIntegerField(
        default=34
    )
    energieprestatie_label_b_meergezinswoning_punten = models.SmallIntegerField(
        default=30
    )
    energieprestatie_label_c_eengezinswoning_punten = models.SmallIntegerField(
        default=22
    )
    energieprestatie_label_c_meergezinswoning_punten = models.SmallIntegerField(
        default=15
    )
    energieprestatie_label_d_eengezinswoning_punten = models.SmallIntegerField(
        default=14
    )
    energieprestatie_label_d_meergezinswoning_punten = models.SmallIntegerField(
        default=11
    )
    energieprestatie_label_e_eengezinswoning_punten = models.SmallIntegerField(
        default=-4
    )
    energieprestatie_label_e_meergezinswoning_punten = models.SmallIntegerField(
        default=-4
    )
    energieprestatie_label_f_eengezinswoning_punten = models.SmallIntegerField(
        default=-9
    )
    energieprestatie_label_f_meergezinswoning_punten = models.SmallIntegerField(
        default=-9
    )
    energieprestatie_label_g_eengezinswoning_punten = models.SmallIntegerField(
        default=-15
    )
    energieprestatie_label_g_meergezinswoning_punten = models.SmallIntegerField(
        default=-15
    )
    energieprestatie_ei_grens_1 = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.60
    )
    energieprestatie_ei_grens_2 = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.80
    )
    energieprestatie_ei_grens_3 = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.20
    )
    energieprestatie_ei_grens_4 = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.40
    )
    energieprestatie_ei_grens_5 = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.80
    )
    energieprestatie_ei_grens_6 = models.DecimalField(
        max_digits=4, decimal_places=2, default=2.10
    )
    energieprestatie_ei_grens_7 = models.DecimalField(
        max_digits=4, decimal_places=2, default=2.40
    )
    energieprestatie_ei_grens_8 = models.DecimalField(
        max_digits=4, decimal_places=2, default=2.70
    )
    energieprestatie_ei_punten_1_eengezinswoning = models.SmallIntegerField(default=52)
    energieprestatie_ei_punten_1_meergezinswoning = models.SmallIntegerField(default=48)
    energieprestatie_ei_punten_2_eengezinswoning = models.SmallIntegerField(default=47)
    energieprestatie_ei_punten_2_meergezinswoning = models.SmallIntegerField(default=43)
    energieprestatie_ei_punten_3_eengezinswoning = models.SmallIntegerField(default=41)
    energieprestatie_ei_punten_3_meergezinswoning = models.SmallIntegerField(default=37)
    energieprestatie_ei_punten_4_eengezinswoning = models.SmallIntegerField(default=34)
    energieprestatie_ei_punten_4_meergezinswoning = models.SmallIntegerField(default=30)
    energieprestatie_ei_punten_5_eengezinswoning = models.SmallIntegerField(default=22)
    energieprestatie_ei_punten_5_meergezinswoning = models.SmallIntegerField(default=15)
    energieprestatie_ei_punten_6_eengezinswoning = models.SmallIntegerField(default=14)
    energieprestatie_ei_punten_6_meergezinswoning = models.SmallIntegerField(default=11)
    energieprestatie_ei_punten_7_eengezinswoning = models.SmallIntegerField(default=-4)
    energieprestatie_ei_punten_7_meergezinswoning = models.SmallIntegerField(default=-4)
    energieprestatie_ei_punten_8_eengezinswoning = models.SmallIntegerField(default=-9)
    energieprestatie_ei_punten_8_meergezinswoning = models.SmallIntegerField(default=-9)
    energieprestatie_ei_punten_9_eengezinswoning = models.SmallIntegerField(default=-15)
    energieprestatie_ei_punten_9_meergezinswoning = models.SmallIntegerField(
        default=-15
    )
    energieprestatie_bouwjaar_grens_1 = models.PositiveSmallIntegerField(default=2002)
    energieprestatie_bouwjaar_grens_2 = models.PositiveSmallIntegerField(default=2000)
    energieprestatie_bouwjaar_grens_3 = models.PositiveSmallIntegerField(default=1992)
    energieprestatie_bouwjaar_grens_4 = models.PositiveSmallIntegerField(default=1984)
    energieprestatie_bouwjaar_grens_5 = models.PositiveSmallIntegerField(default=1979)
    energieprestatie_bouwjaar_grens_6 = models.PositiveSmallIntegerField(default=1977)
    energieprestatie_bouwjaar_punten_1_eengezinswoning = models.SmallIntegerField(
        default=41
    )
    energieprestatie_bouwjaar_punten_1_meergezinswoning = models.SmallIntegerField(
        default=37
    )
    energieprestatie_bouwjaar_punten_2_eengezinswoning = models.SmallIntegerField(
        default=34
    )
    energieprestatie_bouwjaar_punten_2_meergezinswoning = models.SmallIntegerField(
        default=30
    )
    energieprestatie_bouwjaar_punten_3_eengezinswoning = models.SmallIntegerField(
        default=22
    )
    energieprestatie_bouwjaar_punten_3_meergezinswoning = models.SmallIntegerField(
        default=15
    )
    energieprestatie_bouwjaar_punten_4_eengezinswoning = models.SmallIntegerField(
        default=14
    )
    energieprestatie_bouwjaar_punten_4_meergezinswoning = models.SmallIntegerField(
        default=11
    )
    energieprestatie_bouwjaar_punten_5_eengezinswoning = models.SmallIntegerField(
        default=-4
    )
    energieprestatie_bouwjaar_punten_5_meergezinswoning = models.SmallIntegerField(
        default=-4
    )
    energieprestatie_bouwjaar_punten_6_eengezinswoning = models.SmallIntegerField(
        default=-9
    )
    energieprestatie_bouwjaar_punten_6_meergezinswoning = models.SmallIntegerField(
        default=-9
    )
    energieprestatie_bouwjaar_punten_7_eengezinswoning = models.SmallIntegerField(
        default=-15
    )
    energieprestatie_bouwjaar_punten_7_meergezinswoning = models.SmallIntegerField(
        default=-15
    )
    energieprestatie_epv_eengezinswoning_punten = models.SmallIntegerField(default=32)
    energieprestatie_epv_meergezinswoning_punten = models.SmallIntegerField(default=28)
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
    vertrekken = models.JSONField(default=default_extra_ruimten, blank=True)
    overige_ruimten = models.JSONField(default=default_extra_ruimten, blank=True)
    verkeersruimten = models.JSONField(default=default_extra_ruimten, blank=True)
    buitenruimten = models.JSONField(default=default_extra_ruimten, blank=True)
    parkeerruimte_gesloten_garage_bij_complex = models.PositiveIntegerField(default=0)
    parkeerruimte_buiten_bij_complex_met_dak = models.PositiveIntegerField(default=0)
    parkeerruimte_buiten_bij_complex_zonder_dak = models.PositiveIntegerField(default=0)
    energielabel_klasse = models.CharField(max_length=10, null=True, blank=True)
    energie_index = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    energie_index_geldig_voor_wws = models.BooleanField(default=False)
    energieprestatie_registratiedatum = models.DateField(null=True, blank=True)
    energieprestatie_peildatum = models.DateField(null=True, blank=True)
    energieprestatie_individuele_woonruimte = models.BooleanField(default=False)
    is_eengezinswoning = models.BooleanField(null=True, blank=True)
    heeft_energieprestatievergoeding = models.BooleanField(default=False)
    bouwjaar = models.PositiveIntegerField(null=True, blank=True)
    gebruiksoppervlakte = models.PositiveIntegerField(default=0)
    woz_waarde = models.PositiveIntegerField(default=0)
    woz_peildatum_jaar = models.PositiveIntegerField(default=2025)
    woz_kleine_nieuwbouwwoning = models.BooleanField(default=False)
    woz_nieuwbouw_2015_2019 = models.BooleanField(default=False)
    woz_bouwvoltooiingspercentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    woonvoorziening_handicap = models.BooleanField(default=False)
    woonvoorziening_handicap_netto_investering = models.PositiveIntegerField(default=0)
    monument = models.BooleanField(default=False)
    monument_soort = models.CharField(max_length=255, null=True, blank=True)
    bijzondere_voorziening_intercom_met_beeld = models.PositiveIntegerField(default=0)
    bijzondere_voorziening_laadpaal = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.adres} - {self.id}"
