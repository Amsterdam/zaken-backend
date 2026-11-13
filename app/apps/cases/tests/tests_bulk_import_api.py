import base64
import binascii
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from apps.addresses.models import Address
from apps.cases.models import Case, CaseProject, CaseReason, CaseTheme, Subject
from apps.cases.tasks import task_import_bulk_file
from celery import states
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from model_bakery import baker
from openpyxl import Workbook
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from utils.bulk_case_importer import BulkCaseImporter, BulkImportException
from utils.unittest_helpers import get_test_user


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class ProcessBulkFileApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.theme = baker.make(CaseTheme, name="Leegstand")
        cls.reason = baker.make(
            CaseReason,
            theme=cls.theme,
            name="Leegstandsmelding eigenaar",
        )
        cls.subjects = [
            baker.make(Subject, theme=cls.theme, name=name)
            for name in ("Administratieve leegstand", "Professionele eigenaar")
        ]
        cls.url = reverse("cases-process-bulk-file")
        cls.files_path = Path(__file__).parent / "files"

    def setUp(self):
        self.client = APIClient()
        self.user = get_test_user()
        self.client.force_authenticate(user=self.user)

    def upload_file(self, filename, only_theme=False, **data):
        """Upload with the theme, the reason and the subjects; or, with
        `only_theme`, only the theme (checking the addresses before the reason
        is chosen)."""
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
            {
                "file": uploaded_file,
                "theme_id": self.theme.pk,
                **(
                    {}
                    if only_theme
                    else {
                        "reason_id": self.reason.pk,
                        "subject_ids": [subject.pk for subject in self.subjects],
                    }
                ),
                **data,
            },
            format="multipart",
        )

    def run_import_task(self, file_base64, user_id=None):
        return task_import_bulk_file(
            file_base64=file_base64,
            user_id=user_id if user_id is not None else str(self.user.pk),
            theme_id=self.theme.pk,
            reason_id=self.reason.pk,
            subject_ids=[subject.pk for subject in self.subjects],
            project_id=None,
            jump_to=None,
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

    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
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
    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
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
        self.assertEqual(cache.get("bulk-import:import-task-id"), str(self.user.pk))
        self.addCleanup(cache.delete, "bulk-import:import-task-id")
        self.assertEqual(Case.objects.count(), 0)
        mock_bag_search.assert_not_called()
        mock_delay.assert_called_once()
        task_kwargs = json.loads(json.dumps(mock_delay.call_args.kwargs))
        self.assertEqual(task_kwargs["user_id"], str(self.user.pk))
        self.assertEqual(task_kwargs["project_id"], project.pk)

        result = task_import_bulk_file(**task_kwargs)
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
        self.assertTrue(all(case.description for case in Case.objects.all()))

    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_dry_run_needs_only_the_theme(self, mock_bag_search, mock_delay):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]

        response = self.upload_file("example_leegstand_correct.xlsx", only_theme=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["total_processed"], 3)
        self.assertTrue(
            all(case["success"] for case in result["case_data"]),
            result["case_data"],
        )
        self.assertEqual(Case.objects.count(), 0)
        mock_delay.assert_not_called()

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_dry_run_with_only_the_theme_finds_open_cases(self, mock_bag_search):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]
        address = baker.make(Address, bag_id="bag-id-0")
        baker.make(
            Case,
            theme=self.theme,
            reason=self.reason,
            address=address,
            end_date=None,
        )

        response = self.upload_file("example_leegstand_correct.xlsx", only_theme=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_data = response.json()["case_data"]
        self.assertFalse(case_data[0]["success"])
        self.assertEqual(
            case_data[0]["error"],
            "Er bestaat al een open zaak met dit thema op dit adres.",
        )
        # So the user can go to the address and its open case.
        self.assertEqual(case_data[0]["bag_id"], "bag-id-0")
        self.assertTrue(all(case["success"] for case in case_data[1:]))

    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    def test_import_without_reason_is_rejected(self, mock_delay):
        response = self.upload_file(
            "example_leegstand_correct.xlsx", only_theme=True, dry_run=False
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason_id", response.json())
        mock_delay.assert_not_called()

    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    def test_import_needs_what_creating_a_case_needs(self, mock_delay):
        other_theme = baker.make(CaseTheme, name="Kamerverhuur")
        project_reason = baker.make(CaseReason, theme=self.theme, name="Project")
        cases = {
            "reason of another theme": {
                "reason_id": baker.make(CaseReason, theme=other_theme).pk
            },
            "reason Project without a project": {"reason_id": project_reason.pk},
            "project of another theme": {
                "reason_id": project_reason.pk,
                "project_id": baker.make(CaseProject, theme=other_theme).pk,
            },
        }
        for name, data in cases.items():
            with self.subTest(name):
                response = self.upload_file(
                    "example_leegstand_correct.xlsx",
                    only_theme=True,
                    dry_run=False,
                    **data,
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_delay.assert_not_called()

    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    def test_import_rejects_reasons_of_one_case(self, mock_delay):
        for name in ("MMA", "SIG melding", "Digitaal toezicht"):
            with self.subTest(name):
                reason = baker.make(CaseReason, theme=self.theme, name=name)

                response = self.upload_file(
                    "example_leegstand_correct.xlsx",
                    only_theme=True,
                    dry_run=False,
                    reason_id=reason.pk,
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("reason_id", response.json())
        mock_delay.assert_not_called()

    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    def test_import_jumps_to_unoccupied_only_for_leegstand(self, mock_delay):
        mock_delay.return_value.id = "import-task-id"
        self.addCleanup(cache.delete, "bulk-import:import-task-id")
        other_theme = baker.make(CaseTheme, name="Kamerverhuur")
        other_reason = baker.make(CaseReason, theme=other_theme)

        response = self.upload_file(
            "example_leegstand_correct.xlsx",
            only_theme=True,
            dry_run=False,
            theme_id=other_theme.pk,
            reason_id=other_reason.pk,
            jump_to="unoccupied",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("jump_to", response.json())
        mock_delay.assert_not_called()

        # The theme of setUp is Leegstand.
        response = self.upload_file(
            "example_leegstand_correct.xlsx", dry_run=False, jump_to="unoccupied"
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_importer_without_reason_does_not_create_cases(self, mock_bag_search):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]

        with (self.files_path / "example_leegstand_correct.xlsx").open("rb") as file:
            result = BulkCaseImporter(
                file, self.user, theme=self.theme, dry_run=False
            ).import_from_file()

        self.assertEqual(result["total_created"], 0)
        self.assertTrue(
            all(
                not case["success"] and "reason_id" in case["error"]
                for case in result["case_data"]
            ),
            result["case_data"],
        )
        self.assertEqual(Case.objects.count(), 0)

    def upload_workbook(self, rows):
        """Upload an Excel file made of `rows`, with the header in row 2."""
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(["Naam bedrijf", "Bedrijf"])
        worksheet.append(["straat", "postcode", "huisnr", "toevoeging", "toelichting"])
        for row in rows:
            worksheet.append(row)
        file = BytesIO()
        workbook.save(file)
        return self.client.post(
            self.url,
            {
                "file": SimpleUploadedFile("adressen.xlsx", file.getvalue()),
                "theme_id": self.theme.pk,
            },
            format="multipart",
        )

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_rows_have_their_excel_row_number_address_and_error(self, mock_bag_search):
        mock_bag_search.side_effect = [
            self.successful_bag_response(0),
            {"response": {"numFound": 0, "docs": []}},
        ]

        response = self.upload_workbook(
            [
                # The postal code as in the file; in the result as "1074 BT".
                ["Hemonystraat", "1074bt", 66, 3, "Toelichting"],
                [None, None, None, None, None],  # Skipped, but counted.
                ["Linneausstraat", "1093EH", 49, None, "Toelichting"],
                ["Kerkstraat", "1017 GB", "geen nummer", None, "Toelichting"],
            ]
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["case_data"],
            [
                {
                    "row_number": 3,
                    "address": "Hemonystraat 66-3, 1074 BT",
                    "bag_id": "bag-id-0",
                    "success": True,
                    "error": None,
                    "case_id": None,
                },
                {
                    "row_number": 5,
                    "address": "Linneausstraat 49, 1093 EH",
                    "bag_id": None,
                    "success": False,
                    "error": "Adres niet gevonden.",
                    "case_id": None,
                },
                {
                    "row_number": 6,
                    "address": "Kerkstraat geen nummer, 1017 GB",
                    "bag_id": None,
                    "success": False,
                    "error": "Het adres is niet goed ingevuld. Controleer: huisnummer.",
                    "case_id": None,
                },
            ],
        )

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_formula_error_in_description_is_said_in_words(self, mock_bag_search):
        mock_bag_search.return_value = self.successful_bag_response(0)

        response = self.upload_workbook([["Kerkstraat", "1017GB", 27, "D", "#N/B"]])

        self.assertEqual(
            response.json()["case_data"][0]["error"],
            "De toelichting bevat een foute formule (#N/B).",
        )

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_more_than_one_address_found_asks_to_check_the_suffix(
        self, mock_bag_search
    ):
        mock_bag_search.return_value = {
            "response": {
                "numFound": 2,
                "docs": [
                    {
                        "postcode": "1017GB",
                        "huisnummer": 27,
                        "huisnummertoevoeging": "1",
                        "weergavenaam": "Kerkstraat 27-1",
                        "score": 1,
                    },
                    {
                        "postcode": "1017GB",
                        "huisnummer": 27,
                        "huisnummertoevoeging": "2",
                        "weergavenaam": "Kerkstraat 27-2",
                        "score": 1,
                    },
                ],
            }
        }

        response = self.upload_workbook([["Kerkstraat", "1017GB", 27, None, "Tekst"]])

        self.assertEqual(
            response.json()["case_data"][0]["error"],
            "Meerdere adressen gevonden. Controleer de toevoeging.",
        )

    @patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
    @patch("apps.addresses.models.Address.get_or_create_by_bag_id")
    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_description_for_all_cases_comes_above_the_one_of_the_row(
        self, mock_bag_search, mock_delay, mock_address, mock_workflow_delay
    ):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]
        mock_address.side_effect = [
            baker.make(Address, bag_id=f"bag-id-{index}") for index in range(3)
        ]
        mock_delay.return_value.id = "import-task-id"
        self.addCleanup(cache.delete, "bulk-import:import-task-id")

        response = self.upload_file(
            "example_leegstand_correct.xlsx",
            dry_run=False,
            description="  Bulkbeschikking oktober  ",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        task_kwargs = json.loads(json.dumps(mock_delay.call_args.kwargs))
        # Without the spaces around it (trim_whitespace of the serializer).
        self.assertEqual(task_kwargs["description"], "Bulkbeschikking oktober")

        task_import_bulk_file(**task_kwargs)
        self.assertEqual(Case.objects.count(), 3)
        for case in Case.objects.all():
            first, _, row = case.description.partition("\n\n")
            self.assertEqual(first, "Bulkbeschikking oktober")
            # The explanation of the row is kept, below it.
            self.assertTrue(row, case.description)

    def test_description_is_only_the_one_there_is(self):
        with (self.files_path / "example_leegstand_correct.xlsx").open("rb") as file:
            importer = BulkCaseImporter(
                file, self.user, theme=self.theme, description="Voor alle zaken"
            )
            without = BulkCaseImporter(file, self.user, theme=self.theme)

        self.assertEqual(importer._get_description(None), "Voor alle zaken")
        self.assertEqual(importer._get_description(" "), "Voor alle zaken")
        self.assertEqual(
            importer._get_description("Van de rij"), "Voor alle zaken\n\nVan de rij"
        )
        self.assertEqual(without._get_description("Van de rij"), "Van de rij")
        self.assertIsNone(without._get_description(None))

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
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
        self.assertEqual(result["case_data"][0]["error"], "Adres niet gevonden.")
        self.assertEqual(Case.objects.count(), 0)

    @patch("apps.cases.views.case.BulkCaseImporter")
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

    @patch("apps.cases.views.case.BulkCaseImporter")
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
                self.assertFalse("Sensitive" in response.json()["error"])

    def test_file_is_required(self):
        response = self.client.post(
            self.url,
            {"dry_run": False},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.json())

    @patch("apps.cases.views.case.BulkCaseImporter")
    @patch("apps.cases.views.case.task_import_bulk_file.delay")
    def test_file_over_size_limit_is_rejected(self, mock_delay, mock_importer):
        for dry_run in (True, False):
            with self.subTest(dry_run=dry_run):
                file = SimpleUploadedFile("large.xlsx", b"x" * (2 * 1024 * 1024 + 1))
                response = self.client.post(
                    self.url, {"file": file, "dry_run": dry_run}, format="multipart"
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(
                    "File size must not exceed 2 MiB.", response.json()["file"]
                )

        mock_delay.assert_not_called()
        mock_importer.assert_not_called()

    def test_task_rejects_invalid_base64(self):
        with self.assertRaises(binascii.Error):
            self.run_import_task("not base64!")

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_task_returns_row_errors(self, mock_bag_search):
        mock_bag_search.return_value = {"response": {"numFound": 0, "docs": []}}
        with (self.files_path / "example_leegstand_with_errors.xlsx").open(
            "rb"
        ) as file:
            file_base64 = base64.b64encode(file.read()).decode("ascii")

        result = self.run_import_task(file_base64)

        self.assertEqual(result["total_processed"], 1)
        self.assertEqual(result["total_created"], 0)
        self.assertFalse(result["dry_run"])
        self.assertFalse(result["case_data"][0]["success"])
        self.assertEqual(result["case_data"][0]["error"], "Adres niet gevonden.")
        self.assertEqual(Case.objects.count(), 0)

    def test_task_propagates_invalid_excel_error(self):
        file_base64 = base64.b64encode(b"not an Excel file").decode("ascii")
        with self.assertRaisesMessage(BulkImportException, "Kan bestand niet openen"):
            self.run_import_task(file_base64)

    def test_task_requires_existing_user(self):
        user_id = self.user.pk
        self.user.delete()
        with self.assertRaises(get_user_model().DoesNotExist):
            self.run_import_task("", user_id)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class BulkFileStatusApiTest(APITestCase):
    def setUp(self):
        self.user = get_test_user()
        self.client.force_authenticate(user=self.user)
        self.task_id = "bulk-import-status-task"
        self.cache_key = f"bulk-import:{self.task_id}"
        cache.set(self.cache_key, str(self.user.pk), timeout=86400)
        self.addCleanup(cache.delete, self.cache_key)
        self.url = reverse("cases-bulk-import-status", kwargs={"task_id": self.task_id})

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
        task_import_bulk_file.backend.store_result(
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
                {
                    "row_number": 2,
                    "address": "Straat 1, 1234AB",
                    "bag_id": "0363010000000001",
                    "success": True,
                    "error": None,
                    "case_id": 1,
                },
                {
                    "row_number": 3,
                    "address": "Straat 2, 1234AB",
                    "bag_id": None,
                    "success": False,
                    "error": "Adres niet gevonden.",
                    "case_id": None,
                },
            ],
        }
        task_import_bulk_file.backend.store_result(self.task_id, result, states.SUCCESS)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], states.SUCCESS)
        self.assertEqual(response.json()["result"], result)
        self.assertIsNone(response.json()["error"])

    def test_failed_task_does_not_expose_exception_details(self):
        task_import_bulk_file.backend.store_result(
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

    @patch("apps.cases.views.case.task_import_bulk_file.AsyncResult")
    def test_unknown_or_expired_task_returns_not_found(self, mock_result):
        cache.delete(self.cache_key)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_result.assert_not_called()

    @patch("apps.cases.views.case.task_import_bulk_file.AsyncResult")
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
