from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from apps.puntenteller.berekening.helpers import afronden_op_hele_punten, geldend_op
from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import Huurprijsopslag, MaximaleHuurprijs

CENT = Decimal("0.01")


def maximale_huurprijs(
    totaal_punten: Decimal,
    huurprijsopslagen: list[Huurprijsopslag],
    kengetal: Kengetal,
) -> MaximaleHuurprijs | None:
    # Beleidsboek bijlage 3: de maximale huurprijs hoort bij het puntenaantal,
    # volgens de huurprijstabel die nu geldt.
    tabel = geldend_op(kengetal.huurprijstabel_per_ingangsdatum, date.today())
    if tabel is None:
        return None
    ingangsdatum, bedragen = tabel
    bedragen = [Decimal(str(bedrag)) for bedrag in bedragen]
    punten = max(int(afronden_op_hele_punten(totaal_punten)), 0)
    hoogste = len(bedragen) - 1
    if punten <= hoogste:
        bedrag = bedragen[punten]
    else:
        # Beleidsboek 2.1.6: elk punt boven de 250 telt mee met het verschil
        # tussen de bedragen bij 249 en 250 punten.
        bedrag = bedragen[hoogste] + (punten - hoogste) * (
            bedragen[hoogste] - bedragen[hoogste - 1]
        )
    # Beleidsboek 2.13.1: de percentages van de opslagen worden opgeteld en
    # daarna in één keer over de maximale huurprijs berekend.
    procent = sum((o.procent for o in huurprijsopslagen), Decimal("0"))
    met_opslagen = bedrag * (1 + procent / 100)
    return MaximaleHuurprijs(
        bedrag=bedrag.quantize(CENT, rounding=ROUND_HALF_UP),
        met_opslagen=met_opslagen.quantize(CENT, rounding=ROUND_HALF_UP),
        prijspeil=ingangsdatum,
    )
