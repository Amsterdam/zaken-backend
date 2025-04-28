# import requests_mock
# from apps.cases.models import Case, CaseDocument, CaseState
# from apps.openzaak.models import Notification
# from django.core.management import call_command
# from django.test import TestCase, override_settings
# from freezegun import freeze_time
# from model_bakery import baker
# from zgw_consumers.test import mock_service_oas_get

# from .utils import OpenZaakBaseMixin


# class OpenZaakNotificatieTests(OpenZaakBaseMixin, TestCase):
#     def _build_notification(
#         self,
#         main_url,
#         resource_url,
#         resource,
#         channel="zaken",
#         action="create",
#         extra={},
#     ):
#         """
#         kenmerken = {
#             "bronorganisatie": "224557609",
#             "zaaktype": "https://catalogi-api.vng.cloud/api/v1/zaaktypen/53c5c164",
#             "vertrouwelijkheidaanduiding": "openbaar"
#         }
#         """
#         return {
#             "kanaal": channel,
#             "hoofdObject": main_url,
#             "resource": resource,
#             "resourceUrl": resource_url,
#             "actie": action,
#             "aanmaakdatum": "2019-03-27T10:59:13Z",
#             "kenmerken": extra,
#         }

#     @requests_mock.Mocker()
#     def test_handle_no_notification(self, m):
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAK_URL,
#             resource="zaak",
#             action="update",
#         )
#         notification = baker.make(Notification, data=notificatie_body)
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertFalse(notification.processed)

#     @requests_mock.Mocker()
#     def test_handle_case_update_notification(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)

#         case = baker.make(Case, case_url=self.ZAAK_URL)
#         old_description = case.description
#         old_start_date = case.start_date
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAK_URL,
#             resource="zaak",
#             action="update",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         case.refresh_from_db()
#         self.assertNotEqual(case.description, old_description)
#         self.assertNotEqual(case.start_date, old_start_date)

#     @requests_mock.Mocker()
#     def test_handle_case_update_notification_non_existing_case(self, m):
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAK_URL,
#             resource="zaak",
#             action="update",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         self.assertEqual(Case.objects.count(), 0)

#     @requests_mock.Mocker()
#     def test_handle_case_destroy_notification(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)

#         case = baker.make(Case, case_url=self.ZAAK_URL)
#         case.description
#         case.start_date
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAK_URL,
#             resource="zaak",
#             action="destroy",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)

#     @requests_mock.Mocker()
#     def test_handle_case_destroy_notification_no_existing_case(self, m):
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAK_URL,
#             resource="zaak",
#             action="destroy",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)

#     # State is not implemented yet.
#     @override_settings(
#         OPENZAAK_CASETYPEURL_TOEZICHT="https://catalogi.nl/api/v1/statustypen/a5628108-456f-4459-9c9c-4be8c9f67f13"
#     )
#     @requests_mock.Mocker()
#     def test_handle_status_create_notification(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.STATUS_URL, json=self.status, status_code=200)

#         baker.make(Case, case_url=self.ZAAK_URL)
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL, resource_url=self.STATUS_URL, resource="status"
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         self.assertEqual(CaseState.objects.count(), 1)

#     @requests_mock.Mocker()
#     def test_handle_status_create_notification_no_state_type(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.STATUS_URL, json=self.status, status_code=200)

#         baker.make(Case, case_url=self.ZAAK_URL)
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL, resource_url=self.STATUS_URL, resource="status"
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)

#     @requests_mock.Mocker()
#     def test_handle_status_create_notification_no_case(self, m):
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL, resource_url=self.STATUS_URL, resource="status"
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)

#     @requests_mock.Mocker()
#     def test_handle_status_update_notification(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.STATUS_URL, json=self.status, status_code=200)

#         baker.make(Case, case_url=self.ZAAK_URL)
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.STATUS_URL,
#             resource="status",
#             action="update",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         self.assertEqual(CaseState.objects.count(), 0)

#     @requests_mock.Mocker()
#     def test_case_document_create_notification(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(
#             self.ZAAKINFORMATIEOBJECT_URL,
#             json=self.zaakinformatieobject,
#             status_code=200,
#         )
#         m.get(self.DOCUMENT_URL, json=self.document, status_code=200)
#         m.post(
#             f"{self.ZAKEN_ROOT}zaakinformatieobjecten",
#             json=self.zaakinformatieobject,
#             status_code=201,
#         )

#         baker.make(Case, case_url=self.ZAAK_URL)
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAKINFORMATIEOBJECT_URL,
#             resource="zaakinformatieobject",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         self.assertEqual(CaseDocument.objects.count(), 1)
#         self.assertEqual(CaseDocument.objects.filter(connected=True).count(), 1)

#     @requests_mock.Mocker()
#     def test_case_document_create_notification_existing_connection(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(
#             self.ZAAKINFORMATIEOBJECT_URL,
#             json=self.zaakinformatieobject,
#             status_code=200,
#         )
#         m.get(self.DOCUMENT_URL, json=self.document, status_code=200)
#         m.post(
#             f"{self.ZAKEN_ROOT}zaakinformatieobjecten",
#             json=self.zaakinformatieobject,
#             status_code=201,
#         )

#         case = baker.make(Case, case_url=self.ZAAK_URL)
#         case_document = baker.make(
#             CaseDocument, case=case, document_url=self.DOCUMENT_URL, connected=False
#         )
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAKINFORMATIEOBJECT_URL,
#             resource="zaakinformatieobject",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         case_document.refresh_from_db()
#         self.assertTrue(case_document.connected)

#     @requests_mock.Mocker()
#     def test_case_document_create_notification_no_case(self, m):
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAKINFORMATIEOBJECT_URL,
#             resource="zaakinformatieobject",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)

#     @requests_mock.Mocker()
#     def test_case_document_update_notification(self, m):
#         mock_service_oas_get(m, self.ZAKEN_ROOT, "zrc")
#         mock_service_oas_get(m, self.DOCUMENTEN_ROOT, "drc")
#         m.post(f"{self.ZAKEN_ROOT}zaken", json=self.zaak, status_code=201)
#         m.put(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(self.ZAAK_URL, json=self.zaak, status_code=200)
#         m.get(
#             self.ZAAKINFORMATIEOBJECT_URL,
#             json=self.zaakinformatieobject,
#             status_code=200,
#         )
#         m.get(self.DOCUMENT_URL, json=self.document, status_code=200)
#         m.post(
#             f"{self.ZAKEN_ROOT}zaakinformatieobjecten",
#             json=self.zaakinformatieobject,
#             status_code=201,
#         )

#         baker.make(Case, case_url=self.ZAAK_URL)
#         notificatie_body = self._build_notification(
#             main_url=self.ZAAK_URL,
#             resource_url=self.ZAAKINFORMATIEOBJECT_URL,
#             resource="zaakinformatieobject",
#             action="update",
#         )
#         with freeze_time("2022-02-02"):
#             notification = baker.make(
#                 Notification, data=notificatie_body, processed=False
#             )
#         call_command("handle_notifications")
#         notification.refresh_from_db()
#         self.assertTrue(notification.processed)
#         self.assertEqual(CaseDocument.objects.count(), 0)
