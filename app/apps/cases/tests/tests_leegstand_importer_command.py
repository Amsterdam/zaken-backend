from io import StringIO
from pathlib import Path
from unittest.mock import patch

from apps.cases.models import Case, CaseReason, CaseTheme
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from model_bakery import baker
from utils.unittest_helpers import get_test_user

FILE = str(Path(__file__).parent / "files" / "example_leegstand_correct.xlsx")


def bag_response(index):
    return {
        "response": {
            "numFound": 1,
            "docs": [{"adresseerbaarobject_id": f"bag-id-{index}", "weergavenaam": ""}],
        }
    }


class LeegstandImporterCommandTest(TestCase):
    def setUp(self):
        self.user = get_test_user()
        baker.make(CaseTheme, name="Leegstand")

    @patch("utils.bulk_case_importer.do_bag_search_pdok_by_address")
    def test_dry_run_checks_the_rows(self, mock_bag_search):
        mock_bag_search.side_effect = [bag_response(index) for index in range(3)]
        out = StringIO()

        call_command(
            "leegstand_importer", FILE, username=self.user.username, stdout=out
        )

        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("Rij "), lines)
        self.assertTrue(lines[0].endswith(": OK"), lines)
        self.assertIn("processed=3, created=0, dry_run=True", lines[-1])
        self.assertEqual(Case.objects.count(), 0)

    def test_import_needs_a_reason(self):
        with self.assertRaisesMessage(CommandError, "--reason"):
            call_command(
                "leegstand_importer",
                FILE,
                username=self.user.username,
                dry_run=False,
            )

    def test_reason_is_passed_on(self):
        reason = baker.make(CaseReason, theme=CaseTheme.objects.get())
        with patch(
            "apps.cases.management.commands.leegstand_importer.BulkCaseImporter"
        ) as importer:
            importer.return_value.import_from_file.return_value = {
                "case_data": [],
                "total_processed": 0,
                "total_created": 0,
            }
            call_command(
                "leegstand_importer",
                FILE,
                username=self.user.username,
                reason=reason.pk,
                subject=[1, 2],
                dry_run=False,
                stdout=StringIO(),
            )

        kwargs = importer.call_args.kwargs
        self.assertEqual(kwargs["reason"], reason.pk)
        self.assertEqual(kwargs["subjects"], [1, 2])
        self.assertFalse(kwargs["dry_run"])
