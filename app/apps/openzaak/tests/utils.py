from typing import Any, Dict, List

from django.conf import settings
from django.db.models import signals
from model_bakery import baker
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component


class ZakenBackendTestMixin:
    def setUp(self):
        super().setUp()

        self.signals = signals.post_save.receivers
        signals.post_save.receivers = []

        baker.make(
            Service,
            api_type=APITypes.ztc,
            api_root=settings.TEST_CATALOGI_ROOT,
            client_id="aza_amsterdam",
            secret="12345",
            oas=f"{settings.TEST_CATALOGI_ROOT}schema/openapi.yaml",
        )
        baker.make(
            Service,
            api_type=APITypes.drc,
            api_root=settings.TEST_DOCUMENTEN_ROOT,
            client_id="aza_amsterdam",
            secret="12345",
            oas=f"{settings.TEST_DOCUMENTEN_ROOT}schema/openapi.yaml",
        )
        baker.make(
            Service,
            api_type=APITypes.zrc,
            api_root=settings.TEST_ZAKEN_ROOT,
            client_id="aza_amsterdam",
            secret="12345",
            oas=f"{settings.TEST_ZAKEN_ROOT}schema/openapi.yaml",
        )

    def tearDown(self):
        signals.post_save.receivers = self.signals


class OpenZaakBaseMixin(ZakenBackendTestMixin):
    def setUp(self):
        super().setUp()

        self.ZAKEN_ROOT = settings.TEST_ZAKEN_ROOT
        self.DOCUMENTEN_ROOT = settings.TEST_DOCUMENTEN_ROOT
        self.CATALOGI_ROOT = settings.TEST_CATALOGI_ROOT
        self.NOTIFICATION_ROOT = settings.TEST_NOTIFICATION_ROOT

        self.ZAAK_TYPE_URL = (
            f"{self.CATALOGI_ROOT}zaaktypen/e59108b0-ed10-41f8-bbbe-cb7e5546d54c"
        )
        self.STATUS_TYPE_URL = (
            f"{self.CATALOGI_ROOT}statustypen/a5628108-456f-4459-9c9c-4be8c9f67f13"
        )
        self.ZAAK_URL = f"{self.ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"
        self.STATUS_URL = (
            f"{self.ZAKEN_ROOT}statussen/f0875a2d-c128-440e-98cd-a0a2b1e36cad"
        )
        self.ZAAKINFORMATIEOBJECT_URL = f"{self.ZAKEN_ROOT}zaakinformatieobject/4891f0a6-eb17-4477-a060-268c33f5ce57"
        self.DOCUMENT_URL = f"{self.DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/7f77b2a1-2fb5-4e41-b75f-daac19017c1a"

        self.nrc_service = baker.make(
            Service,
            api_type=APITypes.nrc,
            api_root=self.NOTIFICATION_ROOT,
            client_id="notificaties",
            secret="notificaties",
            oas=f"{self.NOTIFICATION_ROOT}schema/openapi.yaml",
        )

        self.zaak_type = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
        )
        self.zaak_type2 = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
        )
        self.zaaktypen = paginated_response([self.zaak_type, self.zaak_type2])

        self.informatie_type = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
        )
        self.informatie_type2 = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
        )
        self.informatieobjecttypen = paginated_response(
            [self.informatie_type, self.informatie_type2]
        )

        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=self.ZAAK_URL,
            startdatum="2022-01-02",
            einddatum=None,
        )

        self.status = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=self.STATUS_URL,
            statustype=self.STATUS_TYPE_URL,
            statustoelichting="Status update",
        )

        self.document = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=self.DOCUMENT_URL,
        )

        self.zaakinformatieobject = generate_oas_component(
            "zrc", "schemas/ZaakInformatieObject", informatieobject=self.DOCUMENT_URL
        )

        self.fout = generate_oas_component(
            "zrc",
            "schemas/Fout",
        )


def paginated_response(results: List[dict]) -> Dict[str, Any]:
    body = {
        "count": len(results),
        "previous": None,
        "next": None,
        "results": results,
    }
    return body
