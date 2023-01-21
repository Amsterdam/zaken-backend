import requests_mock
from apps.cases.models import Case, CaseDocument, CaseTheme
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from model_bakery import baker
from zgw_consumers.test import mock_service_oas_get

from ..helpers import (
    connect_case_and_document,
    create_document,
    create_open_zaak_case,
    create_open_zaak_case_status,
    delete_document,
    get_document,
    get_document_inhoud,
    get_document_types,
    get_documents_meta,
    get_open_zaak_case,
    get_open_zaak_case_document_connection,
    get_open_zaak_case_status,
    get_zaaktype,
    get_zaaktypen,
    update_document,
    update_open_zaak_case,
)
from .utils import OpenZaakBaseMixin


class OpenZaakConnectionTests(OpenZaakBaseMixin, TestCase):
    @requests_mock.Mocker()
    def test_get_case_types(self, m):
        mock_service_oas_get(m, self.CATALOGI_ROOT, "ztc")
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        cases_response = get_zaaktypen()
        self.assertEqual(len(cases_response), 2)
        self.assertIsNotNone(cases_response)

    @requests_mock.Mocker()
    def test_get_case_type(self, m):
        mock_service_oas_get(m, self.CATALOGI_ROOT, "ztc")
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaak_type, status_code=200)
        m.get(f"{self.ZAAK_TYPE_URL}", json=self.zaak_type, status_code=200)
        response = get_zaaktype(self.ZAAK_TYPE_URL)
        self.assertEqual(response.identificatie, "861ec2b4-daf9-4709-9cc0-06476e647269")
        self.assertIsNotNone(response)

    @requests_mock.Mocker()
    def test_get_document_types(self, m):
        mock_service_oas_get(m, self.CATALOGI_ROOT, "ztc")
        m.get(
            f"{self.CATALOGI_ROOT}informatieobjecttypen",
            json=self.informatieobjecttypen,
            status_code=200,
        )
        cases_response = get_document_types()
        self.assertEqual(len(cases_response), 2)
        self.assertIsNotNone(cases_response)

    @requests_mock.Mocker()
    def test_create_open_zaak_case(self, m):
        mock_service_oas_get(m, self.CATALOGI_ROOT, "ztc")
        mock_service_oas_get(
            m,
            self.ZAKEN_ROOT,
            "zrc",
        )
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        create_open_zaak_case(case)
        case.refresh_from_db()
        self.assertEqual(case.case_url, self.ZAAK_URL)

    @requests_mock.Mocker()
    def test_get_open_zaak_case(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
        m.get(self.ZAAK_URL, json=self.zaak)
        data_case = get_open_zaak_case(self.ZAAK_URL)
        self.assertEqual(data_case.url, self.ZAAK_URL)

    @requests_mock.Mocker()
    def test_update_open_zaak_case(self, m):
        m.put(self.ZAAK_URL, json=self.zaak)
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme, case_url=self.ZAAK_URL)
        update_open_zaak_case(case)

    # @requests_mock.Mocker()
    # def test_create_open_zaak_case_state(self, m):
    #     m.post(f"{self.ZAKEN_ROOT}statussen", json=self.status, status_code=201)
    #     m.get(self.ZAAK_URL, json=self.zaak)
    #     theme = baker.make(CaseTheme, name="mock_name")
    #     case = baker.make(Case, theme=theme)
    #     state = baker.make(CaseState, case=case)
    #     create_open_zaak_case_status(state)

    @requests_mock.Mocker()
    def test_get_open_zaak_case_state(self, m):
        m.get(self.STATUS_URL, json=self.status)
        theme = baker.make(CaseTheme, name="mock_name")
        baker.make(Case, theme=theme)
        case_status = get_open_zaak_case_status(self.STATUS_URL)
        self.assertEqual(case_status.url, self.STATUS_URL)

    @requests_mock.Mocker()
    def test_create_document(self, m):
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.post(
            f"{self.DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            json=self.document,
            status_code=201,
        )
        uploaded_file = SimpleUploadedFile(
            "file.txt", b"file_content", content_type="text/plain"
        )
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        case_document = create_document(case, uploaded_file)
        self.assertEqual(case_document.document_url, self.DOCUMENT_URL)

    @requests_mock.Mocker()
    def test_get_document(self, m):
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.get(self.DOCUMENT_URL, json=self.document, status_code=200)
        case_document = get_document(self.DOCUMENT_URL)
        self.assertEqual(case_document.get("url"), self.DOCUMENT_URL)

    @requests_mock.Mocker()
    def test_get_documents_meta(self, m):
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.get(self.DOCUMENT_URL, json=self.document, status_code=200)
        case_document = get_documents_meta([self.DOCUMENT_URL, self.DOCUMENT_URL])
        self.assertEqual(len(case_document), 2)

    @requests_mock.Mocker()
    def test_get_document_inhoud(self, m):
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.get(self.DOCUMENT_DOWNLOAD_URL, json=self.document, status_code=200)
        case_document = get_document_inhoud(self.DOCUMENT_DOWNLOAD_URL)
        self.assertEqual(case_document.__class__, bytes)

    @requests_mock.Mocker()
    def test_update_document(self, m):
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.post(
            f"{self.DOCUMENT_URL}/lock", json={"lock": "lock_string"}, status_code=200
        )
        m.put(self.DOCUMENT_URL, json=self.document, status_code=200)
        m.post(f"{self.DOCUMENT_URL}/unlock", json=None, status_code=204)
        uploaded_file = SimpleUploadedFile(
            "file.txt", b"file_content", content_type="text/plain"
        )
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        document = baker.make(CaseDocument, case=case, document_url=self.DOCUMENT_URL)
        case_document = update_document(document, uploaded_file)
        self.assertEqual(case_document.url, self.DOCUMENT_URL)

    @requests_mock.Mocker()
    def test_delete_document(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        # mock_service_oas_get(m, f"{self.DOCUMENTEN_ROOT}/lock", "drc")
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.delete(
            self.ZAAK_DOCUMENT_URL,
            json=None,
            status_code=204,
        )
        m.post(f"{self.DOCUMENT_URL}/lock", json=None, status_code=200)
        m.delete(self.DOCUMENT_URL, json=None, status_code=204)
        SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        document = baker.make(
            CaseDocument,
            case=case,
            document_url=self.DOCUMENT_URL,
            case_document_connection_url=self.ZAAK_DOCUMENT_URL,
        )
        delete_document(document)

    @requests_mock.Mocker()
    def test_connect_case_and_document(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        m.post(
            "https://zaken.nl/api/v1/zaakinformatieobjecten",
            json=self.zaakinformatieobject,
            status_code=201,
        )
        case_document = baker.make(CaseDocument, document_url=self.DOCUMENT_URL)
        self.assertFalse(case_document.connected)
        connect_case_and_document(case_document)
        case_document.refresh_from_db()
        self.assertTrue(case_document.connected)

    @requests_mock.Mocker()
    def test_get_open_zaak_case_document_connection(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        m.get(self.ZAAKINFORMATIEOBJECT_URL, json=self.zaakinformatieobject)
        case_document = get_open_zaak_case_document_connection(
            self.ZAAKINFORMATIEOBJECT_URL
        )
        self.assertEqual(case_document.get("informatieobject"), self.DOCUMENT_URL)
