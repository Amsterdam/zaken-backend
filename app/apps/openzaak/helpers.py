from datetime import date

from django.conf import settings
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Zaak
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service


def get_default_zaaktype():
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()
    results = ztc_client.list("zaaktype", {"identificatie": settings.DEFAULT_TEAM})
    default_zaaktype = results["results"][0]
    return default_zaaktype


def create_open_zaak_case(identification, description):
    zaak_type = get_default_zaaktype()
    print("Creating Case with zaaktype:")
    print(zaak_type)

    today = date.today().strftime("%Y-%m-%d")
    zaak_body = {
        "identificatie": identification,
        "toelichting": description,
        "zaaktype": zaak_type["url"],
        "bronorganisatie": settings.DEFAULT_CATALOGUS_RSIN,
        "verantwoordelijkeOrganisatie": settings.DEFAULT_CATALOGUS_RSIN,
        "registratiedatum": today,
        "startdatum": today,
    }

    ztc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    zaak = ztc_client.create("zaak", zaak_body)
    result = factory(Zaak, zaak)
    return result
