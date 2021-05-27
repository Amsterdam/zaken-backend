from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service


class Command(BaseCommand):
    help = "Used locally during debugging, since deletion of Zaaktypes isn't allowed through the OpenZaak Admin"
    OAS_SCHEMA = "schema/openapi.yaml"

    def _client_from_url(self, url):
        service = Service.get_service(url)
        return service.build_client()

    def delete_case_type(self):
        ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()
        results = ztc_client.list("zaaktype", {"identificatie": settings.DEFAULT_THEME})

        for result in results["results"]:
            url = result["url"]
            client = self._client_from_url(url)
            client.delete(resource="zaaktype", url=url)

        self.stdout.write(self.style.SUCCESS("Zaaktype deleted"))

    def handle(self, *args, **options):
        try:
            self.delete_case_type()
        except Exception as e:
            raise CommandError("Generic error", e)

        self.stdout.write(self.style.SUCCESS("Done deleting"))
