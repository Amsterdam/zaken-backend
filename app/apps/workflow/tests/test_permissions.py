from unittest.mock import Mock, patch

from apps.users.auth_apps import TopKeyAuth
from apps.users.permissions import CanEditTaskWeekNumber
from apps.workflow.views import CaseUserTaskViewSet
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate


class CaseUserTaskWeekNumberPermissionTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock(is_authenticated=True)
        self.user.has_perm.return_value = False

    def patch_task(self, data):
        request = self.factory.patch("/tasks/1/", data, format="json")
        force_authenticate(request, user=self.user)
        view = CaseUserTaskViewSet.as_view({"patch": "partial_update"})
        with patch.object(
            CaseUserTaskViewSet,
            "partial_update",
            return_value=Response(status=status.HTTP_200_OK),
        ) as update:
            response = view(request, pk=1)
        return response, update

    def test_week_number_requires_permission(self):
        for value in (12, None):
            with self.subTest(value=value):
                response, update = self.patch_task({"week_number": value})

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.user.has_perm.assert_called_with("users.edit_task_week_number")
                update.assert_not_called()

    def test_week_number_allowed_with_permission(self):
        self.user.has_perm.return_value = True
        for value in (12, None):
            with self.subTest(value=value):
                response, update = self.patch_task({"week_number": value})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.user.has_perm.assert_called_with("users.edit_task_week_number")
                update.assert_called_once()

    def test_other_fields_do_not_require_week_number_permission(self):
        response, update = self.patch_task({"name": "Updated task"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.has_perm.assert_not_called()
        update.assert_called_once()

    def test_top_key_does_not_bypass_week_number_permission(self):
        self.user = AnonymousUser()
        with patch.object(TopKeyAuth, "has_permission", return_value=True):
            response, update = self.patch_task({"week_number": 12})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        update.assert_not_called()

    def test_get_does_not_require_week_number_permission(self):
        request = self.factory.get("/tasks/", {"week_number": 12})
        request.user = self.user

        self.assertTrue(CanEditTaskWeekNumber().has_permission(request, None))
        self.user.has_perm.assert_not_called()

    def test_write_methods_check_week_number_permission(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            for value in (12, None):
                for allowed in (False, True):
                    with self.subTest(method=method, value=value, allowed=allowed):
                        self.user.has_perm.reset_mock()
                        self.user.has_perm.return_value = allowed
                        request = Mock(
                            method=method,
                            data={"week_number": value},
                            user=self.user,
                        )

                        self.assertEqual(
                            CanEditTaskWeekNumber().has_permission(request, None),
                            allowed,
                        )
                        self.user.has_perm.assert_called_once_with(
                            "users.edit_task_week_number"
                        )

    def test_safe_methods_do_not_require_week_number_permission(self):
        for method in ("GET", "HEAD", "OPTIONS"):
            with self.subTest(method=method):
                request = Mock(method=method, data={"week_number": 12}, user=self.user)

                self.assertTrue(CanEditTaskWeekNumber().has_permission(request, None))
                self.user.has_perm.assert_not_called()
