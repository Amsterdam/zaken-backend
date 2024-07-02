"""
These are all helpers that are needed to send, request, update and delete the needed information.
Based on: https://github.com/VNG-Realisatie/zaken-api/blob/stable/1.0.x/src/notificaties.md
"""

import base64
import hashlib
import logging
import mimetypes
import pathlib
import uuid
from datetime import date
from typing import List

import requests
from apps.cases.models import CaseDocument
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.api_models.documenten import Document
from zgw_consumers.api_models.zaken import Resultaat, Status, Zaak
from zgw_consumers.concurrent import parallel
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.service import get_paginated_results

logger = logging.getLogger(__name__)


def _get_file_hash(content):
    s = hashlib.sha3_224()
    s.update(content)
    return s.hexdigest()


def _parse_date(date):
    if date:
        return date.strftime("%Y-%m-%d")
    return None


def _get_description(id, zaaktype_identificatie):
    """Get the description based on the zaaktype_identificatie."""
    if zaaktype_identificatie == settings.OPENZAAK_ZAAKTYPE_IDENTIFICATIE_HANDHAVEN:
        description = f"""
        Het dossier ({id}) is nu in de handhavingsfase. Het staat nog niet vast dat gehandhaafd zal worden.
        Uit de onderzoeksresultaten kan bijvoorbeeld volgen dat de woning regulier bewoond wordt
        en dus niet gehandhaafd moet worden, dat het dossier terug moet naar de toezichtfase omdat
        de woning opnieuw bezocht moet worden door de toezichthouders of dat een andere actie benodigd is.
        Handhaving begint eerst met een aanschrijving waarin wij kenbaar maken voornemens zijn om handhavend
        op te treden. Daarop kan een zienswijze worden ingediend. Vervolgens zullen wij nogmaals naar alle
        feiten en omstandigheden kijken en overwegen of een handhavingsbesluit moet worden opgelegd,
        of dat daarvan moet worden afgezien.
        """
    else:
        description = f"""
        Het dossier ({id}) is nu in de toezichtfase. Toezichthouders zullen het adres bezoeken. Houdt u er rekening mee
        dat dit enige tijd kan duren. Het kan bijvoorbeeld voorkomen dat toezichthouders meerdere malen naar het
        adres toe moeten voor hun onderzoek.
        """
    # Remove whitespace caused by indentation and create one single line.
    single_line_string = " ".join(description.replace("\n", " ").split())
    return single_line_string


def _build_zaak_body(
    instance, zaaktype_identificatie=settings.OPENZAAK_ZAAKTYPE_IDENTIFICATIE_TOEZICHT
):
    today = date.today()

    zaaktypen = get_zaaktypen(zaaktype_identificatie)
    zaaktype_url = next(iter([zt.get("url") for zt in zaaktypen]))
    zaaktype_omschrijving = next(iter([zt.get("omschrijving") for zt in zaaktypen]))
    identificatie = f"{instance.id}-{zaaktype_omschrijving}"
    if len(identificatie) > 40:
        print("Open-zaak: Maximum characters for Zaak identificatie exceeded.")
    description = _get_description(instance.id, zaaktype_identificatie)
    return {
        "identificatie": identificatie,
        "toelichting": description[:1000],
        "zaaktype": zaaktype_url,
        "bronorganisatie": settings.DEFAULT_RSIN,
        "verantwoordelijkeOrganisatie": settings.DEFAULT_RSIN,
        "registratiedatum": _parse_date(today),
        "startdatum": _parse_date(instance.start_date),
        "einddatum": _parse_date(instance.end_date),
    }


def _build_document_body(
    file,
    language,
    informatieobjecttype=None,
    lock=None,
):
    file.seek(0)
    content = file.read()
    file_size = len(content)

    string_content = base64.b64encode(content).decode("utf-8")
    informatieobjecttype = (
        informatieobjecttype
        if informatieobjecttype
        else settings.OPENZAAK_DEFAULT_INFORMATIEOBJECTTYPE_URL
    )
    # Get mime type
    try:
        (mime_type, *_) = mimetypes.guess_type(pathlib.Path(file.name))
    except Exception as e:
        logger.info(f"MIME-type cannot be detected: {e}")

    document_body = {
        "identificatie": uuid.uuid4().hex,
        "formaat": mime_type,
        "informatieobjecttype": informatieobjecttype,
        "bronorganisatie": settings.DEFAULT_RSIN,
        "creatiedatum": _parse_date(date.today()),
        "titel": file.name[:200],
        "auteur": settings.DEFAULT_RSIN,
        "taal": language,
        "bestandsnaam": file.name,
        "inhoud": string_content,
        "indicatieGebruiksrecht": False,
        "bestandsomvang": file_size,  # total bytes as integer
    }
    if lock:
        document_body["lock"] = lock

    return document_body


def get_zaaktypen(identificatie=None):
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()

    params = {
        "catalogus": settings.OPENZAAK_CATALOGI_URL,
        "status": "definitief",  # Options: "alles", "definitief", "concept"
        # "page": 1
    }
    if identificatie:
        params.update({"identificatie": identificatie})

    paginated_results = None
    try:
        paginated_results = get_paginated_results(
            ztc_client, "zaaktype", query_params=params
        )
    except Exception as e:
        logger.error(f"ZTC_CLIENT - Cannot fetch zaaktypen: {e}")

    return paginated_results


def get_zaaktype(zaaktype_url):
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()

    response = None
    try:
        response = ztc_client.retrieve(
            "zaaktype",
            url=zaaktype_url,
        )
    except Exception as e:
        logger.error(f"ZTC_CLIENT - Cannot fetch zaaktype by zaaktype_url: {e}")

    return factory(ZaakType, response)


def get_document_types(identificatie=None):
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()
    params = {
        "catalogus": settings.OPENZAAK_CATALOGI_URL,
        "status": "definitief",  # Options: "alles", "definitief", "concept"
        # "page": 1
    }
    if identificatie:
        params.update({"identificatie": identificatie})

    paginated_results = None
    try:
        paginated_results = get_paginated_results(
            ztc_client, "informatieobjecttype", query_params=params
        )
    except Exception as e:
        logger.error(
            f"ZTC_CLIENT - Cannot fetch informatieobjecttypen / document_types: {e}"
        )

    return paginated_results


def create_open_zaak_case(
    instance, zaaktype_identificatie=settings.OPENZAAK_ZAAKTYPE_IDENTIFICATIE_TOEZICHT
):
    zaak_body = _build_zaak_body(instance, zaaktype_identificatie)
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    response = None
    try:
        response = zrc_client.create("zaak", zaak_body)
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot create case: {e}")
        raise e

    result = factory(Zaak, response)
    instance.case_url = result.url
    instance.save()
    return instance


def get_open_zaak_case(case_url):
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    response = None
    try:
        response = zrc_client.retrieve(
            "zaken",
            url=case_url,
            request_kwargs={
                "headers": {
                    "Accept-Crs": "EPSG:4326",
                }
            },
        )
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot fetch case: {e}")

    return factory(Zaak, response)


def update_open_zaak_case(instance):
    #  TODO: It's not possible to change zaaktype
    zaak_body = _build_zaak_body(instance)
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    zrc_client.update("zaak", url=instance.case_url, data=zaak_body)


def get_resultaattypen(zaaktype_url=None):
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()

    params = {
        "status": "definitief",  # Options: "alles", "definitief", "concept"
    }
    if zaaktype_url:
        params.update({"zaaktype": zaaktype_url})

    paginated_results = None
    try:
        paginated_results = get_paginated_results(
            ztc_client, "resultaattype", query_params=params
        )
    except Exception as e:
        logger.error(f"ZTC_CLIENT - Cannot fetch resultaattype: {e}")

    return paginated_results


def create_open_zaak_case_resultaat(
    instance,
    omschrijving_generiek=settings.OPENZAAK_RESULTAATTYPE_OMSCHRIJVING_GENERIEK_AFGEHANDELD,
):
    """
    Create resultaat in open-zaak
    In here we expect a case instance
    """
    case_meta = get_open_zaak_case(instance.case_url)
    resultaattypen = get_resultaattypen(case_meta.zaaktype)
    resultaattype = next(
        (
            r
            for r in resultaattypen
            if r["omschrijvingGeneriek"] == omschrijving_generiek
        ),
        None,
    )
    if resultaattype is None:
        logger.error("Open-zaak error: No resultaattype found")
        return

    omschrijving = resultaattype["omschrijving"]

    resultaat_body = {
        "zaak": instance.case_url,
        "resultaattype": resultaattype["url"],
        "toelichting": f"{omschrijving} in AZA",
    }
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    response = None
    try:
        response = zrc_client.create("resultaat", resultaat_body)
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot create resultaat: {e}")

    factory(Resultaat, response)


def get_statustypen(zaaktype_url=None):
    ztc_client = Service.objects.filter(api_type=APITypes.ztc).get().build_client()

    params = {
        "status": "definitief",  # Options: "alles", "definitief", "concept"
    }
    if zaaktype_url:
        params.update({"zaaktype": zaaktype_url})

    paginated_results = None
    try:
        paginated_results = get_paginated_results(
            ztc_client, "statustype", query_params=params
        )
    except Exception as e:
        logger.error(f"ZTC_CLIENT - Cannot fetch statustypen: {e}")

    return paginated_results


def create_open_zaak_case_status(
    instance,
    omschrijving_generiek=settings.OPENZAAK_STATUSTYPE_OMSCHRIJVING_GENERIEK_AFSLUITEN,
):
    """
    Create status in open-zaak
    In here we expect a case state instance
    """
    case_meta = get_open_zaak_case(instance.case.case_url)
    statustypen = get_statustypen(case_meta.zaaktype)
    statustype = next(
        (r for r in statustypen if r["omschrijvingGeneriek"] == omschrijving_generiek),
        None,
    )
    if statustype is None:
        print("Open-zaak error: Geen statustype gevonden")
        return

    status_body = {
        "zaak": instance.case.case_url,
        "statustype": statustype["url"],
        "datumStatusGezet": timezone.now().isoformat(),
        "statustoelichting": _("Status aangepast in AZA"),
    }
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    response = None
    try:
        response = zrc_client.create("status", status_body)
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot create status: {e}")

    factory(Status, response)


def get_open_zaak_case_status(case_status_url):
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()
    response = None
    try:
        response = zrc_client.retrieve(
            "status",
            url=case_status_url,
        )
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot fetch case status: {e}")

    return factory(Status, response)


def create_document(instance, file, language="nld", informatieobjecttype=None):
    """
    In here we expect a case instance
    """
    document_body = _build_document_body(file, language, informatieobjecttype)

    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()

    response = None
    try:
        response = drc_client.create("enkelvoudiginformatieobject", document_body)
    except Exception as e:
        logger.error(f"DRC_CLIENT - Cannot create document: {e}")
        raise e

    result = factory(Document, response)
    case_document = CaseDocument.objects.create(
        case=instance, document_url=result.url, document_content=result.inhoud
    )
    return case_document


def get_document(document_url):
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()

    response = None
    try:
        response = drc_client.retrieve(
            "zaakinformatieobject",
            url=document_url,
        )
    except Exception as e:
        logger.error(f"DRC_CLIENT - Cannot fetch document: {e}")

    return response


def get_documents_meta(document_urls):
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()

    def get_data_from_client(url):
        try:
            document = drc_client.retrieve("enkelvoudiginformatieobject", url=url)
        except Exception as e:
            logger.error(f"DRC_CLIENT - Cannot fetch document meta: {e}")
            document = {"error": str(e)}
        return document

    with parallel() as executor:
        _documents = executor.map(
            lambda url: get_data_from_client(url),
            document_urls,
        )
    documents: List[dict] = list(_documents)
    return documents


def get_document_inhoud(document_inhoud_url):
    client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    response = None
    try:
        response = requests.get(
            document_inhoud_url,
            headers=client.auth.credentials(),
        )
    except Exception as e:
        logger.error(f"DRC_CLIENT - Cannot fetch document inhoud: {e}")

    response.raise_for_status()
    return response.content


def update_document(case_document, file, language="nld", informatieobjecttype=None):
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    lock = drc_client.request(
        f"{case_document.document_url}/lock",
        "enkelvoudiginformatieobject_lock",
        method="POST",
        json=None,
        expected_status=200,
        request_kwargs={},
    )

    document_body = _build_document_body(
        file, language, informatieobjecttype, lock=lock
    )
    response = drc_client.update(
        "zaakinformatieobject", url=case_document.document_url, data=document_body
    )

    drc_client.request(
        f"{case_document.document_url}/unlock",
        "enkelvoudiginformatieobject_lock",
        method="POST",
        json={"lock": lock},
        expected_status=204,
        request_kwargs={},
    )
    return factory(Document, response)


def delete_document(case_document):
    # open-zaak: delete zaak document connection
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    try:
        zrc_client.delete(
            "zaakinformatieobject", url=case_document.case_document_connection_url
        )
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot delete zaakinformatieobject: {e}")

    # drc: delete document
    drc_client = Service.objects.filter(api_type=APITypes.drc).get().build_client()
    try:
        drc_client.delete("enkelvoudiginformatieobject", url=case_document.document_url)
    except Exception as e:
        logger.error(f"DRC_CLIENT - Cannot delete enkelvoudiginformatieobject: {e}")


def connect_case_and_document(casedocument):
    """
    In here we expect a casedocument instance
    """
    casedocument_body = {
        "informatieobject": casedocument.document_url,
        "zaak": casedocument.case.case_url,
    }

    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    case_document_connection = None
    try:
        case_document_connection = zrc_client.create(
            "zaakinformatieobject", casedocument_body
        )
    except Exception as e:
        logger.error(f"ZRC_CLIENT - Cannot create zaakinformatieobject connection: {e}")

    casedocument.case_document_connection_url = case_document_connection.get("url")
    casedocument.connected = True
    casedocument.save()


def get_open_zaak_case_document_connection(case_document_connection_url):
    zrc_client = Service.objects.filter(api_type=APITypes.zrc).get().build_client()

    response = None
    try:
        response = zrc_client.retrieve(
            "zaakinformatieobject",
            url=case_document_connection_url,
            request_kwargs={
                "headers": {
                    "Accept-Crs": "EPSG:4326",
                }
            },
        )
    except Exception as e:
        logger.error(
            f"ZRC_CLIENT - Cannot fetch zaakinformatieobject with case_document_connection_url: {e}"
        )

    return response
