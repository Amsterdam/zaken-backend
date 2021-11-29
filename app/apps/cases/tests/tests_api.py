import datetime

from apps.addresses.models import Address
from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTheme
from apps.summons.models import SummonType
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class CaseThemeApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_get(self):
        url = reverse("themes-list")
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get(self):
        url = reverse("themes-list")
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        url = reverse("themes-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(data["results"], [])

    def test_authenticated_get_filled(self):
        baker.make(CaseTheme, _quantity=2)

        url = reverse("themes-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(len(data["results"]), 2)


class CaseThemeReasonApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_get(self):
        url = reverse("themes-reasons", kwargs={"pk": 1})

        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_not_found(self):
        url = reverse("themes-reasons", kwargs={"pk": 99})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get(self):
        theme = baker.make(CaseTheme)
        url = reverse("themes-reasons", kwargs={"pk": theme.pk})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        theme = baker.make(CaseTheme)
        url = reverse("themes-reasons", kwargs={"pk": theme.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(data["results"], [])

    def test_authenticated_get_list(self):
        theme = baker.make(CaseTheme)
        baker.make(CaseReason, theme=theme, _quantity=2)

        url = reverse("themes-reasons", kwargs={"pk": theme.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), 2)


class CaseListApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_get(self):
        url = reverse("cases-list")
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_succeed(self):
        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_empty(self):
        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url)
        results = response.data["results"]
        self.assertEqual(results, [])

    def test_get_results(self):
        QUANTITY = 10
        baker.make(Case, _quantity=QUANTITY)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url)
        results = response.data["results"]
        self.assertEqual(len(results), QUANTITY)

    def test_filter_start_date(self):
        # Should only returb dates on the given date and newer
        DATE_A = datetime.datetime.now()
        DATE_B = DATE_A - datetime.timedelta(days=2)
        DATE_C = DATE_A + datetime.timedelta(days=2)

        FILTER_PARAMETERS = {"startDate": DATE_A.strftime("%Y-%m-%d")}

        baker.make(Case, start_date=DATE_A)
        baker.make(Case, start_date=DATE_B)
        baker.make(Case, start_date=DATE_C)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 2)

    def test_filter_date(self):
        # Should only return dates on the given date
        DATE_A = datetime.datetime.now()
        DATE_B = DATE_A - datetime.timedelta(days=2)
        DATE_C = DATE_A + datetime.timedelta(days=2)

        FILTER_PARAMETERS = {"date": DATE_A.strftime("%Y-%m-%d")}

        baker.make(Case, start_date=DATE_A)
        baker.make(Case, start_date=DATE_B)
        baker.make(Case, start_date=DATE_C)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_open_cases(self):
        FILTER_PARAMETERS = {"openCases": "true"}
        CLOSED_CASES_QUANTITY = 10
        OPEN_CASES_QUANTITY = 5

        baker.make(
            Case, end_date=datetime.datetime.now(), _quantity=CLOSED_CASES_QUANTITY
        )
        baker.make(Case, _quantity=OPEN_CASES_QUANTITY)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), OPEN_CASES_QUANTITY)

    def test_filter_closed_cases(self):
        FILTER_PARAMETERS = {"openCases": "false"}
        CLOSED_CASES_QUANTITY = 10
        OPEN_CASES_QUANTITY = 5

        baker.make(
            Case, end_date=datetime.datetime.now(), _quantity=CLOSED_CASES_QUANTITY
        )
        baker.make(Case, _quantity=OPEN_CASES_QUANTITY)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), CLOSED_CASES_QUANTITY)

    def test_filter_theme(self):
        THEME_A = "THEME A"
        THEME_B = "THEME B"

        theme_a = baker.make(CaseTheme, name=THEME_A)
        baker.make(CaseTheme, name=THEME_B)

        baker.make(Case, theme=theme_a)
        url = reverse("cases-list")
        client = get_authenticated_client()

        FILTER_PARAMETERS = {"theme": theme_a.id}
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_reason(self):
        REASON_A = "Reason A"
        REASON_B = "Reason B"

        reason_a = baker.make(CaseReason, name=REASON_A)
        baker.make(CaseReason, name=REASON_B)
        baker.make(Case, reason=reason_a)

        url = reverse("cases-list")
        client = get_authenticated_client()

        FILTER_PARAMETERS = {"reason": reason_a.id}
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_status_same_type(self):
        """
        Cases have same state type, should only return cases with open state
        """
        state_type = baker.make(CaseStateType)
        baker.make(CaseState, status=state_type)
        # Makes closed states
        baker.make(CaseState, end_date=datetime.datetime.now(), status=state_type)
        baker.make(CaseState, end_date=datetime.datetime.now(), status=state_type)

        url = reverse("cases-list")
        client = get_authenticated_client()

        FILTER_PARAMETERS = {"openStatus": state_type.id}
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_status_different_states(self):
        """ Each case has a different state type, should only return one case """
        case_states = baker.make(CaseState, _quantity=10)

        url = reverse("cases-list")
        client = get_authenticated_client()

        test_state = case_states[0]
        FILTER_PARAMETERS = {"openStatus": test_state.status.id}
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)


class CaseCreatApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_post(self):
        url = reverse("cases-list")
        client = get_unauthenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_fail(self):
        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_create(self):
        self.assertEquals(Case.objects.count(), 0)

        theme = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme": theme.pk,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Case.objects.count(), 1)

    def test_authenticated_post_create_fail_wrong_theme(self):
        """ Should not be able to create a case if a wrong theme ID is given """
        theme = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme": 10,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)

    def test_authenticated_post_create_fail_wrong_reason(self):
        """ Should not be able to create a case if a wrong theme ID is given """
        theme = baker.make(CaseTheme)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme": theme.pk,
                "reason": 10,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)

    def test_authenticated_post_create_wrong_theme_reason_relation(self):
        """ Request should fail if the CaseReason is not one of the given themes CaseReasons """
        self.assertEquals(Case.objects.count(), 0)

        theme_a = baker.make(CaseTheme)
        theme_b = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme_a)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme": theme_b.pk,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)

    def test_authenticated_post_create_author(self):
        """
        The author of the case should automatically be set to the authenticated user who made the POST request
        """
        self.assertEquals(Case.objects.count(), 0)

        theme = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme": theme.pk,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        test_user = get_test_user()
        case = Case.objects.get(id=response.data["id"])

        self.assertEquals(case.author, test_user)


class CaseThemeSummonTypeApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_get(self):
        url = reverse("themes-summon-types", kwargs={"pk": 1})

        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_not_found(self):
        url = reverse("themes-summon-types", kwargs={"pk": 1})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get(self):
        summon_type = baker.make(SummonType)
        url = reverse("themes-summon-types", kwargs={"pk": summon_type.theme.pk})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        theme = baker.make(CaseTheme)
        url = reverse("themes-summon-types", kwargs={"pk": theme.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(data["results"], [])

    def test_authenticated_get_list(self):
        theme = baker.make(CaseTheme)
        baker.make(SummonType, theme=theme, _quantity=2)

        url = reverse("themes-summon-types", kwargs={"pk": theme.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), 2)


class CaseSearchApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_get(self):
        url = reverse("cases-search")
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get(self):
        # Should fail if no parameters are given
        url = reverse("cases-search")
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_postal_code_no_number(self):
        url = reverse("cases-search")
        client = get_authenticated_client()

        SEARCH_QUERY_PARAMETERS = {
            "postalCode": "FOO_POSTAL_CODE",
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_street_name_no_number(self):
        url = reverse("cases-search")
        client = get_authenticated_client()

        SEARCH_QUERY_PARAMETERS = {
            "streetName": "FOO_STREET_NUMBER",
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_results(self):
        url = reverse("cases-search")
        client = get_authenticated_client()

        SEARCH_QUERY_PARAMETERS = {
            "streetName": "FOO_STREET_NUMBER",
            "streetNumber": "5",
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()

        self.assertEquals(data["results"], [])

    def test_one_result(self):
        url = reverse("cases-search")
        client = get_authenticated_client()

        MOCK_STREET_NAME = "FOO STREET NAME"
        MOCK_STREET_NUMBER = 5

        address = baker.make(
            Address, street_name=MOCK_STREET_NAME, number=MOCK_STREET_NUMBER
        )
        baker.make(Case, address=address)

        SEARCH_QUERY_PARAMETERS = {
            "streetName": MOCK_STREET_NAME,
            "streetNumber": MOCK_STREET_NUMBER,
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()

        self.assertEquals(len(data["results"]), 1)

    def test_multiple_result(self):
        url = reverse("cases-search")
        client = get_authenticated_client()

        MOCK_STREET_NAME = "FOO STREET NAME"
        MOCK_STREET_NUMBER = 5
        QUANTITY = 3

        address = baker.make(
            Address, street_name=MOCK_STREET_NAME, number=MOCK_STREET_NUMBER
        )
        baker.make(Case, address=address, _quantity=QUANTITY)

        SEARCH_QUERY_PARAMETERS = {
            "streetName": MOCK_STREET_NAME,
            "streetNumber": MOCK_STREET_NUMBER,
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()

        self.assertEquals(len(data["results"]), QUANTITY)

    def test_multiple_address_result(self):
        url = reverse("cases-search")
        client = get_authenticated_client()

        MOCK_STREET_NAME = "FOO STREET NAME"
        MOCK_STREET_NUMBER = 5

        address_a = baker.make(
            Address,
            street_name=MOCK_STREET_NAME,
            number=MOCK_STREET_NUMBER,
            suffix="A",
        )
        address_b = baker.make(
            Address,
            street_name=MOCK_STREET_NAME,
            number=MOCK_STREET_NUMBER,
            suffix="B",
        )

        baker.make(Case, address=address_a)
        baker.make(Case, address=address_b)

        SEARCH_QUERY_PARAMETERS = {
            "streetName": MOCK_STREET_NAME,
            "streetNumber": MOCK_STREET_NUMBER,
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()

        self.assertEquals(len(data["results"]), 2)

    def test_results_open_cases(self):
        """
        Should only returns cases which haven't ended yet
        """
        url = reverse("cases-search")
        client = get_authenticated_client()

        MOCK_STREET_NAME = "FOO STREET NAME"
        MOCK_STREET_NUMBER = 5

        address = baker.make(
            Address, street_name=MOCK_STREET_NAME, number=MOCK_STREET_NUMBER
        )

        baker.make(Case, address=address)

        # Closed cases
        baker.make(
            Case, address=address, end_date=datetime.datetime.now(), _quantity=10
        )

        SEARCH_QUERY_PARAMETERS = {
            "streetName": MOCK_STREET_NAME,
            "streetNumber": MOCK_STREET_NUMBER,
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()

        self.assertEquals(len(data["results"]), 1)

    def test_results_theme_filter(self):
        """
        Should only returns cases for the given theme
        """
        url = reverse("cases-search")
        client = get_authenticated_client()

        MOCK_STREET_NAME = "FOO STREET NAME"
        MOCK_STREET_NUMBER = 5
        MOCK_THEME = "The A-Theme"

        address = baker.make(
            Address, street_name=MOCK_STREET_NAME, number=MOCK_STREET_NUMBER
        )
        theme_a = baker.make(CaseTheme, name=MOCK_THEME)
        theme_b = baker.make(CaseTheme)

        baker.make(Case, theme=theme_a, address=address)
        baker.make(Case, theme=theme_b, address=address)

        SEARCH_QUERY_PARAMETERS = {
            "streetName": MOCK_STREET_NAME,
            "streetNumber": MOCK_STREET_NUMBER,
            "theme": theme_a.id,
        }
        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()

        self.assertEquals(len(data["results"]), 1)

    def test_ton_ids_filter(self):
        """Search for cases that contain the supplied TON IDs."""
        # TODO: this test hasn't been completely run yet due too psycopg errors when creating a Case
        url = reverse("cases-search")
        client = get_authenticated_client()

        MOCK_TON_IDS = [1, 2, 3]
        MOCK_STREET_NAME = "FOO STREET NAME"
        MOCK_STREET_NUMBER = 5

        address = baker.make(
            Address, street_name=MOCK_STREET_NAME, number=MOCK_STREET_NUMBER
        )

        baker.make(Case, address=address, ton_ids=MOCK_TON_IDS)

        SEARCH_QUERY_PARAMETERS = {
            "streetName": MOCK_STREET_NAME,
            "streetNumber": MOCK_STREET_NUMBER,
            "tonIds": ",".join([str(_id) for _id in MOCK_TON_IDS])
        }

        response = client.get(url, SEARCH_QUERY_PARAMETERS)
        data = response.json()
        self.assertEquals(len(data["results"]), 1)
        self.assertEquals(data["results"][0]["ton_ids"], MOCK_TON_IDS)
