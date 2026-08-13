from unittest.mock import patch

from apps.addresses.models import Address
from apps.cases.models import Case
from apps.cases.tasks import task_update_is_bed_and_breakfast_cases
from django.conf import settings
from django.core import management
from django.test import TestCase
from model_bakery import baker


class CaseTasksTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    @patch("apps.cases.tasks.get_is_bed_and_breakfast_for_bag_id")
    def test_task_update_is_bed_and_breakfast_cases(self, mock_get_status):
        vakantieverhuur_theme = baker.make(
            "cases.CaseTheme",
            name=settings.DEFAULT_THEME,
        )
        other_theme = baker.make("cases.CaseTheme")
        vacation_reason = baker.make("cases.CaseReason", theme=vakantieverhuur_theme)
        other_reason = baker.make("cases.CaseReason", theme=other_theme)

        open_address = baker.make(Address, bag_id="bag-open", nummeraanduiding_id="1")
        closed_address = baker.make(
            Address,
            bag_id="bag-closed",
            nummeraanduiding_id="2",
        )
        other_address = baker.make(Address, bag_id="bag-other", nummeraanduiding_id="3")

        open_case = baker.make(
            Case,
            theme=vakantieverhuur_theme,
            reason=vacation_reason,
            address=open_address,
            end_date=None,
            is_bed_and_breakfast=False,
        )
        closed_case = baker.make(
            Case,
            theme=vakantieverhuur_theme,
            reason=vacation_reason,
            address=closed_address,
            is_bed_and_breakfast=False,
        )
        other_case = baker.make(
            Case,
            theme=other_theme,
            reason=other_reason,
            address=other_address,
            end_date=None,
            is_bed_and_breakfast=False,
        )
        closed_case.close_case()

        mock_get_status.side_effect = lambda bag_id: bag_id == "bag-open"

        result = task_update_is_bed_and_breakfast_cases()

        open_case.refresh_from_db()
        closed_case.refresh_from_db()
        other_case.refresh_from_db()

        self.assertTrue(open_case.is_bed_and_breakfast)
        self.assertFalse(closed_case.is_bed_and_breakfast)
        self.assertFalse(other_case.is_bed_and_breakfast)
        self.assertEqual(
            result,
            "task_update_is_bed_and_breakfast_cases: updated 1 cases",
        )
        mock_get_status.assert_called_once_with("bag-open")
