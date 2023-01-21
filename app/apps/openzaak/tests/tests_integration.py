import requests_mock
from apps.cases.models import Case, CaseDocument, CaseState, CaseTheme
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from model_bakery import baker
from zds_client.client import ClientError
from zgw_consumers.test import mock_service_oas_get

from ..helpers import (
    connect_case_and_document,
    create_document,
    create_open_zaak_case,
    create_open_zaak_case_status,
)
from .utils import OpenZaakBaseMixin


class OpenZaakConnectionTests(OpenZaakBaseMixin, TestCase):
    @requests_mock.Mocker()
    def test_uploads_success(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
        m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
        m.post(f"{self.ZAKEN_ROOT}statussen", json=self.status, status_code=201)
        m.post(
            f"{self.DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            json=self.document,
            status_code=201,
        )
        m.post(
            f"{self.ZAKEN_ROOT}zaakinformatieobjecten",
            json=self.zaakinformatieobject,
            status_code=201,
        )

        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        create_open_zaak_case(case)
        # Making sure that the case_url is set
        case.refresh_from_db()
        self.assertEqual(case.case_url, self.ZAAK_URL)

        # State is not implemented yet.
        case_state = baker.make(CaseState, case=case)
        # create_open_zaak_case_status(case_state)
        case_state.refresh_from_db()
        # self.assertTrue(case_state.set_in_open_zaak)

        # Try uploading the document.
        file = SimpleUploadedFile(name="test_file.txt", content=b"Test")
        create_document(case, file, language="nld")
        self.assertEquals(CaseDocument.objects.count(), 1)
        document = CaseDocument.objects.first()
        connect_case_and_document(document)
        document.refresh_from_db()
        self.assertTrue(document.connected)

    @requests_mock.Mocker()
    def test_create_case_failure(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        m.post(f"{self.ZAKEN_ROOT}zaken", json=self.fout, status_code=400)
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        with self.assertRaises(ClientError):
            create_open_zaak_case(case)
        case.refresh_from_db()
        self.assertEqual(case.case_url, None)

    @requests_mock.Mocker()
    def test_create_document_failure(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
        m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
        m.post(
            f"{self.DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            json=self.fout,
            status_code=400,
        )
        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        create_open_zaak_case(case)
        file = SimpleUploadedFile(name="test_file.txt", content=b"Test")
        with self.assertRaises(ClientError):
            create_document(case, file, language="nld")
        self.assertEquals(CaseDocument.objects.count(), 0)

    @requests_mock.Mocker()
    def test_fail_connection(self, m):
        mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
        m.get(f"{self.CATALOGI_ROOT}zaaktypen", json=self.zaaktypen, status_code=200)
        m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
        m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
        m.post(
            f"{self.DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            json=self.document,
            status_code=201,
        )
        m.post(
            f"{self.ZAKEN_ROOT}zaakinformatieobjecten", json=self.fout, status_code=400
        )

        theme = baker.make(CaseTheme, name="mock_name")
        case = baker.make(Case, theme=theme)
        create_open_zaak_case(case)

        # Making sure that the case_url is set
        case.refresh_from_db()
        self.assertEqual(case.case_url, self.ZAAK_URL)

        # Try uploading the document.
        file = SimpleUploadedFile(name="test_file.txt", content=b"Test")
        create_document(case, file, language="nld")
        self.assertEquals(CaseDocument.objects.count(), 1)
        document = CaseDocument.objects.first()
        self.assertFalse(document.connected)
