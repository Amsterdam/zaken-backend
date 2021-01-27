from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service


class Command(BaseCommand):
    help = "Initializes OpenZaak consumers and data structures"
    OAS_SCHEMA = "schema/openapi.yaml"

    def _client_from_url(self, url):
        service = Service.get_service(url)
        return service.build_client()

    def create_zaaktypen_consumer(self):
        API_ROOT = (
            f"{settings.OPEN_ZAAK_HOST}/catalogi/api/{settings.OPEN_ZAAK_API_VERSION}"
        )
        OAS = f"{API_ROOT}/{self.OAS_SCHEMA}"

        service, _ = Service.objects.get_or_create(
            label="Zaaktypen",
            api_type=APITypes.ztc,
        )
        service.api_root = API_ROOT
        service.client_id = settings.OPEN_ZAAK_CLIENT
        service.secret = settings.OPEN_ZAAK_SECRET_KEY
        service.oas = OAS
        service.save()

        self.stdout.write(self.style.SUCCESS("Created or updated Zaaktypen consumer"))

    def create_zaken_consumer(self):

        API_ROOT = (
            f"{settings.OPEN_ZAAK_HOST}/zaken/api/{settings.OPEN_ZAAK_API_VERSION}"
        )
        OAS = f"{API_ROOT}/{self.OAS_SCHEMA}"

        service, _ = Service.objects.get_or_create(
            label="Zaken",
            api_type=APITypes.zrc,
        )
        service.api_root = API_ROOT
        service.client_id = settings.OPEN_ZAAK_CLIENT
        service.secret = settings.OPEN_ZAAK_SECRET_KEY
        service.oas = OAS
        service.save()

        self.stdout.write(self.style.SUCCESS("Created Zaken consumer"))

    def create_catalogus(self):
        ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()
        results = ztc_client.list(
            "catalogus", {"rsin": settings.DEFAULT_CATALOGUS_RSIN}
        )
        if results["count"] == 0:
            body = {
                "naam": settings.DEFAULT_CATALOGUS,
                "domein": settings.DEFAULT_CATALOGUS.upper(),
                "rsin": settings.DEFAULT_CATALOGUS_RSIN,
                "contactpersoonBeheerNaam": "Not niet bekend",
            }
            ztc_client.create("catalogus", body)
            self.stdout.write(self.style.SUCCESS("Created catalogus"))
        else:
            self.stdout.write(self.style.SUCCESS("Catalogus already created"))

    def create_case_type(self):
        ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()
        results = ztc_client.list("zaaktype", {"identificatie": settings.DEFAULT_TEAM})

        if results["count"] == 0:
            catalogus = ztc_client.list(
                "catalogus", {"rsin": settings.DEFAULT_CATALOGUS_RSIN}
            )["results"][0]
            today = date.today().strftime("%Y-%m-%d")

            body = {
                "identificatie": settings.DEFAULT_TEAM,
                "omschrijving": settings.DEFAULT_TEAM,
                "vertrouwelijkheidaanduiding": "vertrouwelijk",
                "doel": settings.DEFAULT_TEAM,
                "aanleiding": settings.DEFAULT_TEAM,
                "indicatieInternOfExtern": "intern",
                "handelingInitiator": settings.DEFAULT_TEAM,
                "onderwerp": settings.DEFAULT_TEAM,
                "handelingBehandelaar": settings.DEFAULT_TEAM,
                "doorlooptijd": "P1Y0M0D",
                "opschortingEnAanhoudingMogelijk": True,
                "verlengingMogelijk": False,
                "publicatieIndicatie": True,
                "productenOfDiensten": [
                    "http://www.amsterdam.nl",
                ],
                "referentieproces": {"naam": settings.DEFAULT_TEAM},
                "catalogus": catalogus["url"],
                "besluittypen": [],
                "gerelateerdeZaaktypen": [],
                "beginGeldigheid": today,
                "versiedatum": today,
            }

            zaaktype = ztc_client.create("zaaktype", body)
            zaaktype_url = zaaktype["url"]

            try:
                client = self._client_from_url(zaaktype_url)
                client.request(
                    f"{zaaktype_url}/publish",
                    "zaaktype_publish",
                    "POST",
                    expected_status=201,
                )
            except AssertionError:
                # For some reason publishing throws an assertion error, but still works.
                pass

            self.stdout.write(self.style.SUCCESS("Created zaaktype"))
        else:
            self.stdout.write(self.style.SUCCESS("Zaaktype already created"))

    def handle(self, *args, **options):
        try:
            self.create_zaken_consumer()
            self.create_zaaktypen_consumer()
            self.create_catalogus()
            self.create_case_type()
        except Exception as e:
            raise CommandError("Generic error", e)

        self.stdout.write(self.style.SUCCESS("Done initialising"))
