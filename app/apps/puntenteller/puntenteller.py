from decimal import Decimal
from typing import TYPE_CHECKING

from apps.puntenteller.models import Kengetal

if TYPE_CHECKING:
    from apps.puntenteller.models import Gebruikersinvoer


class Puntenteller:
    gebruikersinvoer: "Gebruikersinvoer"
    kengetal: Kengetal

    def __init__(self, gebruikersinvoer: "Gebruikersinvoer"):
        self.gebruikersinvoer = gebruikersinvoer
        self.kengetal = Kengetal.objects.first()
        if not self.kengetal:
            raise Kengetal.DoesNotExist("Geen kengetal configuratie gevonden")

    def bereken(self):
        totaal = Decimal("0")
        totaal += self._badkamer_punten()
        totaal += self._keuken_punten()
        totaal += self._apart_toilet_punten()
        totaal += self._vertrekken_punten()
        totaal += self._overige_ruimten_punten()
        totaal += self._verwarming_punten()
        totaal += self._verkoeling_punten()
        totaal += self._buitenruimte_punten()
        totaal += self._parkeerruimte_punten()
        totaal += self._bijzondere_voorzieningen_punten()
        return float(totaal)

    def _badkamer_punten(self):
        subtotal = Decimal("0")
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_toilet_hangend)
            * self.kengetal.badkamer_toilet_hangend_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_toilet_normaal)
            * self.kengetal.badkamer_toilet_normaal_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_wastafel)
            * self.kengetal.badkamer_wastafel_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_meerpersoons_wastafel)
            * self.kengetal.badkamer_meerpersoons_wastafel_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_douche)
            * self.kengetal.badkamer_douche_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_bad)
            * self.kengetal.badkamer_bad_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_baddouche)
            * self.kengetal.badkamer_baddouche_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_bubbelfunctie_bad)
            * self.kengetal.badkamer_bubbelfunctie_bad_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_volledige_afscheiding_douche)
            * self.kengetal.badkamer_volledige_afscheiding_douche_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_handdoekenradiator)
            * self.kengetal.badkamer_handdoekenradiator_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_kast_bij_wastafel)
            * self.kengetal.badkamer_kast_bij_wastafel_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_kastruimte)
            * self.kengetal.badkamer_kastruimte_factor
        )
        # Stopcontacten tellen maximaal twee keer mee.
        subtotal += (
            Decimal(
                min(
                    self._aantal_of_nul(self.gebruikersinvoer.badkamer_stopcontacten),
                    self.kengetal.badkamer_stopcontacten_max,
                )
            )
            * self.kengetal.badkamer_stopcontacten_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_eenhandsmengkraan)
            * self.kengetal.badkamer_eenhandsmengkraan_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_thermostatische_mengkraan)
            * self.kengetal.badkamer_thermostatische_mengkraan_factor
        )
        return subtotal * self._waarde(self.gebruikersinvoer.badkamer_aantal_adressen)

    def _keuken_punten(self):
        subtotal = self._keuken_aanrecht_punten()
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_afzuiginstallatie)
            * self.kengetal.keuken_inbouw_afzuiginstallatie_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_kookplaat_inductie)
            * self.kengetal.keuken_inbouw_kookplaat_inductie_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_kookplaat_keramisch)
            * self.kengetal.keuken_inbouw_kookplaat_keramisch_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_kookplaat_gas)
            * self.kengetal.keuken_inbouw_kookplaat_gas_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_koelkast)
            * self.kengetal.keuken_inbouw_koelkast_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_vrieskast)
            * self.kengetal.keuken_inbouw_vrieskast_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_oven_elektrisch)
            * self.kengetal.keuken_inbouw_oven_elektrisch_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_oven_gas)
            * self.kengetal.keuken_inbouw_oven_gas_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_magnetron)
            * self.kengetal.keuken_inbouw_magnetron_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_vaatwasmachine)
            * self.kengetal.keuken_inbouw_vaatwasmachine_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_extra_kastruimte)
            * self.kengetal.keuken_extra_kastruimte_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_eenhandsmengkraan)
            * self.kengetal.keuken_eenhandsmengkraan_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_thermostatische_mengkraan)
            * self.kengetal.keuken_thermostatische_mengkraan_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_kokendwaterfunctie)
            * self.kengetal.keuken_kokendwaterfunctie_factor
        )
        return subtotal * self._waarde(self.gebruikersinvoer.keuken_aantal_adressen)

    def _keuken_aanrecht_punten(self):
        meters = self._waarde(self.gebruikersinvoer.keuken_aanrechtlengte_meters)
        if meters < self.kengetal.keuken_aanrecht_grens_1:
            return self.kengetal.keuken_aanrecht_punten_1
        if meters < self.kengetal.keuken_aanrecht_grens_2:
            return self.kengetal.keuken_aanrecht_punten_2
        if meters < self.kengetal.keuken_aanrecht_grens_3:
            return self.kengetal.keuken_aanrecht_punten_3
        if meters <= self.kengetal.keuken_aanrecht_grens_4:
            return self.kengetal.keuken_aanrecht_punten_4
        return self.kengetal.keuken_aanrecht_punten_5

    def _apart_toilet_punten(self):
        totaal = Decimal("0")
        totaal += (
            self._waarde(self.gebruikersinvoer.apart_toilet_staand)
            * self.kengetal.apart_toilet_staand_factor
        )
        totaal += (
            self._waarde(self.gebruikersinvoer.apart_toilet_hangend)
            * self.kengetal.apart_toilet_hangend_factor
        )
        return totaal

    def _vertrekken_punten(self):
        factor = self.kengetal.vertrekken_factor
        totaal = self._waarde(self.gebruikersinvoer.vertrekken_oppervlakte) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_1) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_2) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_3) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_4) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_5) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_6) * factor
        return totaal

    def _overige_ruimten_punten(self):
        factor = self.kengetal.overige_ruimte_factor
        totaal = self._waarde(self.gebruikersinvoer.overige_ruimte_oppervlakte) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_1) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_2) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_3) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_4) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_5) * factor
        return totaal

    def _verwarming_punten(self):
        totaal = (
            self._waarde(self.gebruikersinvoer.verwarming_aantal_vertrekken)
            * self.kengetal.verwarming_aantal_vertrekken_factor
        )
        # Overige ruimten en verkeersruimten hebben een maximum van vier punten.
        totaal += (
            Decimal(
                min(
                    self._aantal_of_nul(
                        self.gebruikersinvoer.verwarming_aantal_overige_ruimten
                    ),
                    self.kengetal.verwarming_aantal_overige_ruimten_max,
                )
            )
            * self.kengetal.verwarming_aantal_overige_ruimten_factor
        )
        return totaal

    def _verkoeling_punten(self):
        # Koeling telt voor maximaal twee vertrekken mee.
        return (
            Decimal(
                min(
                    self._aantal_of_nul(
                        self.gebruikersinvoer.verkoeling_aantal_vertrekken
                    ),
                    self.kengetal.verkoeling_aantal_vertrekken_max,
                )
            )
            * self.kengetal.verkoeling_aantal_vertrekken_factor
        )

    def _buitenruimte_punten(self):
        totaal = Decimal("0")
        totaal += (
            self._waarde(self.gebruikersinvoer.buitenruimte_prive_buitenruimte)
            * self.kengetal.buitenruimte_prive_buitenruimte_factor
        )
        totaal += (
            self._waarde(
                self.gebruikersinvoer.buitenruimte_gemeenschappelijke_buitenruimte
            )
            * self.kengetal.buitenruimte_gemeenschappelijke_buitenruimte_factor
        )
        if (
            self._aantal_of_nul(
                self.gebruikersinvoer.buitenruimte_gemeenschappelijke_buitenruimte
            )
            == 0
        ):
            totaal -= self.kengetal.buitenruimte_geen_gemeenschappelijke_aftrek
        return totaal

    def _parkeerruimte_punten(self):
        totaal = Decimal("0")
        totaal += (
            self._waarde(
                self.gebruikersinvoer.parkeerruimte_gesloten_garage_bij_complex
            )
            * self.kengetal.parkeerruimte_gesloten_garage_bij_complex_factor
        )
        totaal += (
            self._waarde(self.gebruikersinvoer.parkeerruimte_buiten_bij_complex_met_dak)
            * self.kengetal.parkeerruimte_buiten_bij_complex_met_dak_factor
        )
        totaal += (
            self._waarde(
                self.gebruikersinvoer.parkeerruimte_buiten_bij_complex_zonder_dak
            )
            * self.kengetal.parkeerruimte_buiten_bij_complex_zonder_dak_factor
        )
        return totaal

    def _bijzondere_voorzieningen_punten(self):
        totaal = Decimal("0")
        totaal += (
            self._waarde(
                self.gebruikersinvoer.bijzondere_voorziening_intercom_met_beeld
            )
            * self.kengetal.bijzondere_voorziening_intercom_met_beeld_factor
        )
        totaal += (
            self._waarde(self.gebruikersinvoer.bijzondere_voorziening_laadpaal)
            * self.kengetal.bijzondere_voorziening_laadpaal_factor
        )
        return totaal

    def _waarde(self, waarde: Decimal | int | None) -> Decimal:
        return Decimal(str(waarde or 0))

    def _aantal_of_nul(self, aantal: int | None) -> int:
        return aantal or 0
