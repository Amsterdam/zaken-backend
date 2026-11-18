from apps.workflow.models import CaseUserTask
from apps.workflow.views import CaseUserTaskFilter
from django.http import QueryDict
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError


class CaseUserTaskFilterTest(SimpleTestCase):
    def get_queryset(self, data):
        task_filter = CaseUserTaskFilter(
            data=QueryDict(data), queryset=CaseUserTask.objects.all()
        )
        self.assertTrue(task_filter.is_valid(), task_filter.errors)
        return task_filter.qs

    def test_week_filters_by_one_or_more_values(self):
        for value, expected in (
            ("week_number=12", [12]),
            ("week_number=12&week_number=13", [12, 13]),
        ):
            with self.subTest(value=value):
                lookup = self.get_queryset(value).query.where.children[0]
                self.assertEqual(lookup.lhs.target.name, "week_number")
                self.assertEqual(lookup.lookup_name, "in")
                self.assertEqual(lookup.rhs, expected)

    def test_week_preserves_other_filters(self):
        queryset = self.get_queryset("week_number=12&completed=false")
        lookups = {
            lookup.lhs.target.name: lookup.rhs
            for lookup in queryset.query.where.children
        }
        self.assertEqual(lookups, {"week_number": [12], "completed": False})

    def test_week_omitted_or_empty_does_not_filter(self):
        for data in ("", "week_number="):
            with self.subTest(data=data):
                self.assertEqual(self.get_queryset(data).query.where.children, [])

    def test_invalid_week_is_rejected(self):
        for value in (
            "week_number=invalid",
            "week_number=12&week_number=invalid",
            "week_number=12.5",
            "week_number=12,13",
            "week_number=None",
            "week_number=12&week_number=None",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    self.get_queryset(value)
