from apps.events.tests.tests_helpers import EventEmitterTestCase
from django.urls import reverse
from rest_framework import status

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class CaseEventGetDetailAPITest(EventEmitterTestCase):
    def test_unauthenticated_get(self):
        url = reverse("cases-detail", kwargs={"pk": 1})
        url += "events/"
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_no_case(self):
        url = reverse("cases-detail", kwargs={"pk": 1})
        url += "events/"
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get_no_events(self):
        case = self.create_case()
        url = reverse("cases-detail", kwargs={"pk": case.id})
        url += "events/"

        client = get_authenticated_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_authenticated_get_events(self):
        case = self.create_case()
        EMIT_COUNT = 4

        for i in range(EMIT_COUNT):
            CaseEventGetDetailAPITest.SubclassEventEmitter.objects.create(case=case)

        url = reverse("cases-detail", kwargs={"pk": case.id})
        url += "events/"

        client = get_authenticated_client()
        response = client.get(url)

        self.assertEqual(len(response.data), EMIT_COUNT)
