from pathlib import Path
from unittest.mock import patch

from apps.cases.models import Case, CaseReason, CaseTheme, Subject
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from utils.unittest_helpers import get_test_user


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
        self.client.force_authenticate(user=get_test_user())

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

    @patch("utils.bulk_leegstand_importer.do_bag_search_pdok_by_address")
    def test_correct_file_defaults_to_dry_run(self, mock_bag_search):
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

    @patch("utils.bulk_leegstand_importer.do_bag_search_pdok_by_address")
    def test_correct_file_creates_cases_when_not_dry_run(self, mock_bag_search):
        mock_bag_search.side_effect = [
            self.successful_bag_response(index) for index in range(3)
        ]

        response = self.upload_file(
            "example_leegstand_correct.xlsx",
            dry_run=False,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["total_processed"], 3)
        self.assertEqual(result["total_created"], 3)
        self.assertFalse(result["dry_run"])
        self.assertTrue(all(case["success"] for case in result["case_data"]))
        self.assertEqual(Case.objects.count(), 3)
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

    def test_file_is_required(self):
        response = self.client.post(
            self.url,
            {"dry_run": False},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.json())
