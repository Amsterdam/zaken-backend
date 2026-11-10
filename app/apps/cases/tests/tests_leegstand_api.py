import base64
import binascii
import json
from pathlib import Path
from unittest.mock import patch

from apps.addresses.models import Address
from apps.cases.models import Case, CaseProject, CaseReason, CaseTheme, Subject
from apps.cases.tasks import task_import_leegstand
from celery import states
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from utils.bulk_leegstand_importer import BulkImportException
from utils.unittest_helpers import get_test_user


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class ProcessLeegstandFileApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.theme = baker.make(CaseTheme, name="Leegstand")
        baker.make(
            CaseReason,
            theme=cls.theme,
            name="Leegstandsmelding eigenaar",
        )
        for name in ("Administratieve leegstand", "Professionele eigenaar"):
            baker.make(Subject, theme=cls.theme, name=name)
        cls.url = reverse("cases-process-leegstand-file")
        cls.files_path = Path(__file__).parent / "files"

    def setUp(self):
        self.client = APIClient()
        self.user = get_test_user()
        self.client.force_authenticate(user=self.user)

    def upload_file(self, filename, **data):
        path = self.files_path / filename
        with path.open("rb") as file:
            uploaded_file = SimpleUploadedFile(
                path.name,
                file.read(),
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
        return self.client.post(
            self.url,
            {"file": uploaded_file, **data},
            format="multipart",
        )

    @staticmethod
    def successful_bag_response(index):
        return {
            "response": {
                "numFound": 1,
                "docs": [
                    {"adresseerbaarobject_id": f"bag-id-{index}", "weergavenaam": ""}
                ],
            }
        }

    @patch("apps.cases.views.case.task_import_leegstand.delay")
    @patch("utils.bulk_leegstand_importer.do_bag_search_pdok_by_address")
    def test_correct_file_defaults_to_dry_run(self, mock_bag_search, mock_delay):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]

        response = self.upload_file("example_leegstand_correct.xlsx")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["total_processed"], 3)
        self.assertEqual(result["total_created"], 0)
        self.assertTrue(result["dry_run"])
        self.assertEqual(len(result["case_data"]), 3)
        self.assertTrue(all(case["success"] for case in result["case_data"]))
        self.assertEqual(Case.objects.count(), 0)
        self.assertEqual(mock_bag_search.call_count, 3)
        mock_delay.assert_not_called()

    @patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
    @patch("apps.addresses.models.Address.get_or_create_by_bag_id")
    @patch("apps.cases.views.case.task_import_leegstand.delay")
    @patch("utils.bulk_leegstand_importer.do_bag_search_pdok_by_address")
    def test_correct_file_creates_cases_in_task_when_not_dry_run(
        self, mock_bag_search, mock_delay, mock_address, mock_workflow_delay
    ):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]
        mock_address.side_effect = [
            baker.make(Address, bag_id=f"bag-id-{index}") for index in range(3)
        ]
        mock_delay.return_value.id = "import-task-id"
        project = baker.make(CaseProject, theme=self.theme)

        response = self.upload_file(
            "example_leegstand_correct.xlsx",
            dry_run=False,
            project_id=project.pk,
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.json(), {"task_id": "import-task-id"})
        self.assertEqual(cache.get("leegstand-import:import-task-id"), str(self.user.pk))
        self.addCleanup(cache.delete, "leegstand-import:import-task-id")
        self.assertEqual(Case.objects.count(), 0)
        mock_bag_search.assert_not_called()
        mock_delay.assert_called_once()
        task_kwargs = json.loads(json.dumps(mock_delay.call_args.kwargs))
        self.assertEqual(task_kwargs["user_id"], str(self.user.pk))
        self.assertEqual(task_kwargs["project_id"], project.pk)

        result = task_import_leegstand(**task_kwargs)
        self.assertEqual(result["total_processed"], 3)
        self.assertEqual(result["total_created"], 3)
        self.assertFalse(result["dry_run"])
        self.assertTrue(all(case["success"] for case in result["case_data"]))
        self.assertEqual(Case.objects.count(), 3)
        self.assertTrue(
            all(
                case.author_id == self.user.pk and case.project_id == project.pk
                for case in Case.objects.all()
            )
        )
        self.assertTrue(
            all(
                case.description.startswith(
                    "Leegstand gemeld: Voorbeeld bedrijf op 06-11-2026."
                )
                for case in Case.objects.all()
            )
        )

    @patch("utils.bulk_leegstand_importer.do_bag_search_pdok_by_address")
    def test_file_with_unmatched_address_returns_row_error(self, mock_bag_search):
        mock_bag_search.return_value = {"response": {"numFound": 0, "docs": []}}

        response = self.upload_file("example_leegstand_with_errors.xlsx")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["total_processed"], 1)
        self.assertEqual(result["total_created"], 0)
        self.assertTrue(result["dry_run"])
        self.assertEqual(len(result["case_data"]), 1)
        self.assertFalse(result["case_data"][0]["success"])
        self.assertIn("No such address found", result["case_data"][0]["msg"])
        self.assertEqual(Case.objects.count(), 0)

    @patch("apps.cases.views.case.BulkLeegstandImporter")
    def test_bulk_import_exception_returns_message(self, mock_importer):
        for stage in ("initialization", "execution"):
            with self.subTest(stage=stage):
                mock_importer.side_effect = None
                mock_importer.return_value.import_from_file.side_effect = None
                error = BulkImportException("Cannot locate header!")
                if stage == "initialization":
                    mock_importer.side_effect = error
                else:
                    mock_importer.return_value.import_from_file.side_effect = error

                response = self.upload_file("example_leegstand_correct.xlsx")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.json(), {"error": "Cannot locate header!"})

    @patch("apps.cases.views.case.BulkLeegstandImporter")
    def test_unexpected_import_exception_returns_generic_error(self, mock_importer):
        for stage in ("initialization", "execution"):
            with self.subTest(stage=stage):
                mock_importer.side_effect = None
                mock_importer.return_value.import_from_file.side_effect = None
                error = RuntimeError("Sensitive internal details")
                if stage == "initialization":
                    mock_importer.side_effect = error
                else:
                    mock_importer.return_value.import_from_file.side_effect = error

                response = self.upload_file("example_leegstand_correct.xlsx")

                self.assertEqual(
                    response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                self.assertFalse("Sensitive" in response.json()['error'])

    def test_file_is_required(self):
        response = self.client.post(
            self.url,
            {"dry_run": False},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.json())

    @patch("apps.cases.views.case.BulkLeegstandImporter")
    @patch("apps.cases.views.case.task_import_leegstand.delay")
    def test_file_over_size_limit_is_rejected(self, mock_delay, mock_importer):
        for dry_run in (True, False):
            with self.subTest(dry_run=dry_run):
                file = SimpleUploadedFile("large.xlsx", b"x" * (2 * 1024 * 1024 + 1))
                response = self.client.post(
                    self.url, {"file": file, "dry_run": dry_run}, format="multipart"
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("File size must not exceed 2 MiB.", response.json()["file"])

        mock_delay.assert_not_called()
        mock_importer.assert_not_called()

    def test_task_rejects_invalid_base64(self):
        with self.assertRaises(binascii.Error):
            task_import_leegstand("not base64!", self.user.pk)

    @patch("utils.bulk_leegstand_importer.do_bag_search_pdok_by_address")
    def test_task_returns_row_errors(self, mock_bag_search):
        mock_bag_search.return_value = {"response": {"numFound": 0, "docs": []}}
        with (self.files_path / "example_leegstand_with_errors.xlsx").open("rb") as file:
            file_base64 = base64.b64encode(file.read()).decode("ascii")

        result = task_import_leegstand(file_base64, str(self.user.pk))

        self.assertEqual(result["total_processed"], 1)
        self.assertEqual(result["total_created"], 0)
        self.assertFalse(result["dry_run"])
        self.assertFalse(result["case_data"][0]["success"])
        self.assertIn("No such address found", result["case_data"][0]["msg"])
        self.assertEqual(Case.objects.count(), 0)

    def test_task_propagates_invalid_excel_error(self):
        file_base64 = base64.b64encode(b"not an Excel file").decode("ascii")
        with self.assertRaisesMessage(BulkImportException, "Failed to read Excel file"):
            task_import_leegstand(file_base64, self.user.pk)

    def test_task_requires_existing_user(self):
        user_id = self.user.pk
        self.user.delete()
        with self.assertRaises(get_user_model().DoesNotExist):
            task_import_leegstand("", user_id)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class LeegstandFileStatusApiTest(APITestCase):
    def setUp(self):
        self.user = get_test_user()
        self.client.force_authenticate(user=self.user)
        self.task_id = "leegstand-status-task"
        self.cache_key = f"leegstand-import:{self.task_id}"
        cache.set(self.cache_key, str(self.user.pk), timeout=86400)
        self.addCleanup(cache.delete, self.cache_key)
        self.url = reverse(
            "cases-leegstand-file-status", kwargs={"task_id": self.task_id}
        )

    def test_pending_task(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "task_id": self.task_id,
                "status": states.PENDING,
                "result": None,
                "error": None,
            },
        )

    def test_started_task(self):
        task_import_leegstand.backend.store_result(
            self.task_id, {"pid": 123, "hostname": "worker"}, states.STARTED
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], states.STARTED)
        self.assertIsNone(response.json()["result"])
        self.assertIsNone(response.json()["error"])

    def test_successful_task_returns_import_result(self):
        result = {
            "total_processed": 2,
            "total_created": 1,
            "dry_run": False,
            "case_data": [
                {"success": True, "msg": "OK"},
                {"success": False, "msg": "No such address found"},
            ],
        }
        task_import_leegstand.backend.store_result(self.task_id, result, states.SUCCESS)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], states.SUCCESS)
        self.assertEqual(response.json()["result"], result)
        self.assertIsNone(response.json()["error"])

    def test_failed_task_does_not_expose_exception_details(self):
        task_import_leegstand.backend.store_result(
            self.task_id, ValueError("internal details"), states.FAILURE
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], states.FAILURE)
        self.assertIsNone(response.json()["result"])
        self.assertEqual(
            response.json()["error"], "Import failed. Contact support with the task ID."
        )
        self.assertNotIn("internal details", response.content.decode())

    @patch("apps.cases.views.case.task_import_leegstand.AsyncResult")
    def test_unknown_or_expired_task_returns_not_found(self, mock_result):
        cache.delete(self.cache_key)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_result.assert_not_called()

    @patch("apps.cases.views.case.task_import_leegstand.AsyncResult")
    def test_other_users_task_returns_not_found(self, mock_result):
        other_user = baker.make(get_user_model())
        self.client.force_authenticate(user=other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_result.assert_not_called()

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
