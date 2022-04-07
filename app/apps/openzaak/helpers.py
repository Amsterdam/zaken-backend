"""
These are all helpers that are needed to send, request, update and delete the needed information.
Based on: https://github.com/VNG-Realisatie/zaken-api/blob/stable/1.0.x/src/notificaties.md
"""

import hashlib
from datetime import date, datetime

from apps.cases.models import CaseDocument, CaseState
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.documenten import Document
from zgw_consumers.api_models.zaken import Status, Zaak
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service


def _get_file_hash(content):
    s = hashlib.sha3_224()
    s.update(content)
    return s.hexdigest()


def _parse_date(date):
    if date:
        return date.strftime("%Y-%m-%d")
    return None


def _build_zaak_body(instance):
    today = date.today()
    return {
        "identificatie": f"{instance.id}{instance.identification}",
        "toelichting": instance.description or "Zaak aangemaakt via AZA",
        "zaaktype": instance.theme.case_type_url,
        "bronorganisatie": settings.DEFAULT_RSIN,
        "verantwoordelijkeOrganisatie": settings.DEFAULT_RSIN,
        "registratiedatum": _parse_date(today),
        "startdatum": _parse_date(instance.start_date),
        "einddatum": _parse_date(instance.end_date),
    }


def _build_document_body(file, title, language, lock=None):
    file.seek(0)
    content = file.read()
    string_content = content.decode("utf-8")

    document_body = {
        "bronorganisatie": settings.DEFAULT_RSIN,
        "creatiedatum": _parse_date(date.today()),
        "titel": title,
        "auteur": settings.DEFAULT_RSIN,
        "taal": language,
        "bestandsnaam": file.name,
        "formaat": file.size,
        "inhoud": string_content,
        "informatieobjecttype": settings.OPENZAAK_DEFAULT_INFORMATIEOBJECTTYPE,
        "ontvangstdatum": _parse_date(date.today()),
        "verzenddatum": _parse_date(date.today()),
        "ondertekening": {"soort": "analoog", "datum": _parse_date(date.today())},
        "integriteit": {
            "algoritme": "sha_3",
            "waarde": _get_file_hash(content),
            "datum": _parse_date(date.today()),
        },
    }
    if lock:
        document_body["lock"] = lock

    return document_body


def get_case_types():
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()

    params = {
        "catalogus": settings.OPENZAAK_CATALOGI_URL,
        "status": "definitief",  # Options: "alles", "definitief", "concept"
        # "page": 1
    }

    response = ztc_client.list("zaaktype", query_param=params)
    return response


def get_document_types():
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()

    params = {
        "catalogus": settings.OPENZAAK_CATALOGI_URL,
        "status": "definitief",  # Options: "alles", "definitief", "concept"
        # "page": 1
    }

    response = ztc_client.list("informatieobjecttype", query_param=params)
    return response


def create_open_zaak_case(instance):
    zaak_body = _build_zaak_body(instance)
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    response = zrc_client.create("zaak", zaak_body)
    result = factory(Zaak, response)
    instance.case_url = result.url
    instance.save()


def get_open_zaak_case(case_url):
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    response = zrc_client.retrieve(
        "zaken",
        url=case_url,
        request_kwargs={
            "headers": {
                "Accept-Crs": "EPSG:4326",
            }
        },
    )
    return factory(Zaak, response)


def update_open_zaak_case(instance):
    zaak_body = _build_zaak_body(instance)
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    zrc_client.update("zaak", url=instance.case_url, data=zaak_body)


def create_open_zaak_case_state(instance):
    """
    In here we expect a case state instance
    """
    now = timezone.now()
    with_time = datetime.combine(instance.created, now.time())

    state_type_url = settings.OPENZAAK_CASETYPEURL_DEFAULT
    if instance.status == CaseState.CaseStateChoice.TOEZICHT and settings.OPENZAAK_CASETYPEURL_TOEZICHT:
        state_type_url = settings.OPENZAAK_CASETYPEURL_TOEZICHT
    if instance.status == CaseState.CaseStateChoice.HANDHAVING and settings.OPENZAAK_CASETYPEURL_HANDHAVING:
        state_type_url = settings.OPENZAAK_CASETYPEURL_HANDHAVING
    if instance.status == CaseState.CaseStateChoice.AFGESLOTEN and settings.OPENZAAK_CASETYPEURL_AFGESLOTEN:
        state_type_url = settings.OPENZAAK_CASETYPEURL_AFGESLOTEN

    status_body = {
        "zaak": instance.case.case_url,
        "statustype": state_type_url,
        "datumStatusGezet": with_time.isoformat(),
        "statustoelichting": _("Status aangepast in AZA"),
    }
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    response = zrc_client.create("status", status_body)
    factory(Status, response)
    instance.set_in_open_zaak = True
    instance.save()


def get_open_zaak_case_state(case_state_url):
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    response = zrc_client.retrieve(
        "status",
        url=case_state_url,
        request_kwargs={
            "headers": {
                "Accept-Crs": "EPSG:4326",
            }
        },
    )
    return factory(Status, response)


def create_document(instance, file, title, language="nld"):
    """
    In here we expect a case instance
    """
    document_body = _build_document_body(file, title, language)

    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    response = drc_client.create("enkelvoudiginformatieobject", document_body)
    result = factory(Document, response)
    case_document = CaseDocument.objects.create(
        case=instance, document_url=result.url, document_content=result.inhoud
    )
    return case_document


def get_document(document_url):
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    response = drc_client.retrieve(
        "zaakinformatieobject",
        url=document_url,
        request_kwargs={
            "headers": {
                "Accept-Crs": "EPSG:4326",
            }
        },
    )
    return factory(Document, response)


def update_document(case_document, file, title, language="nld"):
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    lock = drc_client.request(
        f"{case_document.document_url}/lock",
        "enkelvoudiginformatieobject_lock",
        method="POST",
        json=None,
        expected_status=200,
        request_kwargs={},
    )

    document_body = _build_document_body(file, title, language, lock=lock)
    response = drc_client.update(
        "zaakinformatieobject", url=case_document.document_url, data=document_body
    )

    unlock = drc_client.request(
        f"{case_document.document_url}/unlock",
        "enkelvoudiginformatieobject_lock",
        method="POST",
        json={"lock": lock},
        expected_status=204,
        request_kwargs={},
    )
    return factory(Document, response)


def delete_document(case_document):
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    drc_client.delete("zaakinformatieobject", url=case_document.document_url)


def connect_case_and_document(casedocument):
    """
    In here we expect a casedocument instance
    """
    casedocument_body = {
        "informatieobject": casedocument.document_url,
        "zaak": casedocument.case.case_url,
    }

    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    zrc_client.create("zaakinformatieobject", casedocument_body)
    casedocument.connected = True
    casedocument.save()


def get_open_zaak_case_document_connection(case_document_connection_url):
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    response = zrc_client.retrieve(
        "zaakinformatieobject",
        url=case_document_connection_url,
        request_kwargs={
            "headers": {
                "Accept-Crs": "EPSG:4326",
            }
        },
    )
    return response
