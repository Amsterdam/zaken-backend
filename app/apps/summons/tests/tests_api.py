from apps.cases.models import Case
from apps.summons.models import Summon, SummonedPerson, SummonType
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class SummonCreateAPITest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_post(self):
        url = reverse("summons-list")
        client = get_unauthenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_fail(self):
        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_create(self):
        self.assertEquals(Summon.objects.count(), 0)

        case = baker.make(Case)
        summon_type = baker.make(SummonType, theme=case.theme)

        data = {
            "description": "foo_description",
            "case": case.id,
            "type": summon_type.id,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "preposition": "foo_preposition",
                    "last_name": "foo_last_name",
                },
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Summon.objects.count(), 1)

    def test_authenticated_post_creates_persons(self):
        self.assertEquals(SummonedPerson.objects.count(), 0)

        case = baker.make(Case)
        summon_type = baker.make(SummonType, theme=case.theme)

        data = {
            "description": "foo_description",
            "case": case.id,
            "type": summon_type.id,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "preposition": "foo_preposition",
                    "last_name": "foo_last_name",
                }
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(SummonedPerson.objects.count(), 1)

    def test_authenticated_post_creates_persons_with_preposition(self):
        """
        SummonedPersons can be created with a preposition
        """
        self.assertEquals(SummonedPerson.objects.count(), 0)

        case = baker.make(Case)
        summon_type = baker.make(SummonType, theme=case.theme)

        PREPOSITION = "foo_preposition"
        data = {
            "description": "foo_description",
            "case": case.id,
            "type": summon_type.id,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "preposition": PREPOSITION,
                    "last_name": "foo_last_name",
                },
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        persons = response.json()["persons"]

        self.assertEquals(
            SummonedPerson.objects.get(id=persons[0]["id"]).preposition, PREPOSITION
        )

    def test_authenticated_post_creates_persons_without_preposition(self):
        """
        SummonedPersons can be created without a preposition
        """
        self.assertEquals(SummonedPerson.objects.count(), 0)

        case = baker.make(Case)
        summon_type = baker.make(SummonType, theme=case.theme)

        data = {
            "description": "foo_description",
            "case": case.id,
            "type": summon_type.id,
            "case_user_task_id": 42,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "last_name": "foo_last_name",
                },
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        persons = response.json()["persons"]

        self.assertEquals(
            SummonedPerson.objects.get(id=persons[0]["id"]).preposition, None
        )

    def test_authenticated_post_create_hidden_author(self):
        """
        The current user should be set implicitly as author
        """
        self.assertEquals(SummonedPerson.objects.count(), 0)

        case = baker.make(Case)
        summon_type = baker.make(SummonType, theme=case.theme)

        data = {
            "description": "foo_description",
            "case": case.id,
            "type": summon_type.id,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "preposition": "foo_preposition",
                    "last_name": "foo_last_name",
                },
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        test_user = get_test_user()
        summon = Summon.objects.get(id=response.data["id"])
        self.assertEquals(test_user, summon.author)

    def test_authenticated_post_invalid_case(self):
        """
        A post should fail if the given Case doesn't exist
        """
        self.assertEquals(Summon.objects.count(), 0)

        case = baker.make(Case)
        summon_type = baker.make(SummonType, theme=case.theme)

        data = {
            "description": "foo_description",
            "case": 99,
            "type": summon_type.id,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "preposition": "foo_preposition",
                    "last_name": "foo_last_name",
                }
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Summon.objects.count(), 0)

    def test_authenticated_post_invalid_type(self):
        """
        A post should fail if the given Case doesn't exist
        """
        self.assertEquals(Summon.objects.count(), 0)

        case = baker.make(Case)

        data = {
            "description": "foo_description",
            "case": case.id,
            "type": 99,
            "persons": [
                {
                    "first_name": "foo_first_name",
                    "preposition": "foo_preposition",
                    "last_name": "foo_last_name",
                }
            ],
        }

        url = reverse("summons-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Summon.objects.count(), 0)
