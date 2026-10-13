from apps.puntenteller.berekening.buitenruimte import (
    buitenruimte_rubriek,
    parkeren_rubriek,
)
from apps.puntenteller.berekening.correcties import (
    afronding_opslag,
    huurprijsopslagen,
    rijksmonument_extra_punten,
    zorgwoning_opslag,
)
from apps.puntenteller.berekening.energieprestatie import energieprestatie_rubriek
from apps.puntenteller.berekening.gemeenschappelijk import (
    gemeenschappelijke_ruimten_rubriek,
)
from apps.puntenteller.berekening.helpers import afgerond_op_kwart_punt, som
from apps.puntenteller.berekening.keuken import keuken_rubriek
from apps.puntenteller.berekening.oppervlakte import (
    overige_ruimten_rubriek,
    vertrekken_rubriek,
)
from apps.puntenteller.berekening.sanitair import sanitair_rubriek
from apps.puntenteller.berekening.verwarming import verwarming_en_verkoeling_rubriek
from apps.puntenteller.berekening.voorzieningen import (
    bijzondere_voorzieningen_rubriek,
    woonvoorzieningen_handicap_rubriek,
)
from apps.puntenteller.berekening.woz import (
    nieuwbouw_2015_2019_regels,
    nieuwbouw_2015_2019_uitzondering,
    woz_cap_regels,
    woz_minimum_nieuwbouw_rubriek,
    woz_rubriek,
)
from apps.puntenteller.models import Gebruikersinvoer, Kengetal
from apps.puntenteller.resultaat import PuntentellerResultaat
from apps.puntenteller.ruimte_types import maak_ruimten


class Puntenteller:
    def __init__(self, gebruikersinvoer: Gebruikersinvoer):
        self.gebruikersinvoer = gebruikersinvoer
        self.kengetal = Kengetal.objects.first()
        if not self.kengetal:
            raise Kengetal.DoesNotExist("Geen kengetal configuratie gevonden")
        self.ruimten = maak_ruimten(gebruikersinvoer)

    def bereken(self) -> float:
        return float(self.bereken_resultaat().totaal_punten)

    def bereken_resultaat(self) -> PuntentellerResultaat:
        invoer, ruimten, kengetal = self.gebruikersinvoer, self.ruimten, self.kengetal

        # Beleidsboek zelfstandige woonruimte januari 2026, hoofdstuk 2:
        # de puntentelling wordt opgebouwd uit rubrieken die samen het totaal vormen.
        woz = woz_rubriek(invoer, ruimten, kengetal)
        bijzondere_voorzieningen = bijzondere_voorzieningen_rubriek(invoer, kengetal)
        rubrieken = [
            vertrekken_rubriek(ruimten, kengetal),
            overige_ruimten_rubriek(ruimten, kengetal),
            verwarming_en_verkoeling_rubriek(ruimten, kengetal),
            energieprestatie_rubriek(invoer, kengetal),
            keuken_rubriek(ruimten, kengetal),
            sanitair_rubriek(ruimten, kengetal),
            woonvoorzieningen_handicap_rubriek(invoer, kengetal),
            buitenruimte_rubriek(ruimten, kengetal),
            gemeenschappelijke_ruimten_rubriek(invoer, ruimten, kengetal),
            parkeren_rubriek(ruimten, kengetal),
            woz,
            bijzondere_voorzieningen,
        ]
        for rubriek in rubrieken:
            rubriek.regels = afgerond_op_kwart_punt(rubriek.regels)

        # WOZ-cap en de uitzondering voor nieuwbouw 2015-2019 hangen af van de
        # punten in de overige rubrieken (1 t/m 10 en 12).
        overige_punten = som(r.punten for r in rubrieken if r is not woz)
        nieuwbouw_uitzondering = nieuwbouw_2015_2019_uitzondering(
            invoer, overige_punten
        )
        woz.regels += nieuwbouw_2015_2019_regels(invoer, overige_punten)
        # Beleidsboek 2.11.7: de cap gaat over het totale puntenaantal. Net als
        # de Huurcommissie tellen de extra punten voor een rijksmonument daarin mee.
        rijksmonument = rijksmonument_extra_punten(invoer, kengetal)
        woz.regels += woz_cap_regels(
            woz.punten,
            overige_punten + (rijksmonument.punten if rijksmonument else 0),
            invoer,
            nieuwbouw_uitzondering,
        )
        woz_minimum = woz_minimum_nieuwbouw_rubriek(woz.punten, nieuwbouw_uitzondering)
        if woz_minimum:
            rubrieken.insert(rubrieken.index(woz) + 1, woz_minimum)

        # Opslagen in punten. De zorgwoningtoeslag gaat alleen over rubriek 1 t/m
        # 11.1, dus zonder bijzondere voorzieningen en het WOZ-minimum.
        zorgwoning_basis = som(
            r.punten
            for r in rubrieken
            if r is not bijzondere_voorzieningen and r is not woz_minimum
        )
        opslagen = [
            opslag
            for opslag in (
                zorgwoning_opslag(zorgwoning_basis, invoer, kengetal),
                rijksmonument,
            )
            if opslag
        ]
        totaal = som(r.punten for r in [*rubrieken, *opslagen])
        afronding = afronding_opslag(totaal, opslagen)
        if afronding:
            opslagen.append(afronding)
            totaal += afronding.punten

        return PuntentellerResultaat(
            rubrieken=rubrieken,
            opslagen=opslagen,
            huurprijsopslagen=huurprijsopslagen(invoer, kengetal, totaal),
        )
