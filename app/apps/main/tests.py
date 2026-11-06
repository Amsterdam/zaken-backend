from unittest.mock import patch

from apps.cases.models import Case, CaseReason, CaseTheme
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APITestCase
from utils.unittest_helpers import get_authenticated_client


@patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
class RelatedOrderingFilterTest(APITestCase):
    """Rows with equal sort values get a stable order on id, in the same direction"""

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()
        theme = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme)
        # Same start_date (today) for all cases
        self.case_ids = [
            baker.make(Case, theme=theme, reason=reason).id for _ in range(3)
        ]

    def get_ids(self, ordering):
        response = get_authenticated_client().get(
            reverse("cases-list"), {"ordering": ordering}
        )
        return [case["id"] for case in response.json()["results"]]

    def test_descending_adds_descending_id(self, *args):
        self.assertEqual(self.get_ids("-start_date"), sorted(self.case_ids)[::-1])

    def test_ascending_adds_ascending_id(self, *args):
        self.assertEqual(self.get_ids("start_date"), sorted(self.case_ids))

    def test_explicit_id_is_respected(self, *args):
        self.assertEqual(self.get_ids("-start_date,id"), sorted(self.case_ids))
