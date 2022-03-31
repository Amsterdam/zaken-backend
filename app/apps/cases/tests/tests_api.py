import datetime

from apps.cases.models import (
    Advertisement,
    Case,
    CaseReason,
    CaseStateType,
    CaseTheme,
    CitizenReport,
)
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from apps.summons.models import SummonType
from apps.workflow.models import CaseWorkflow
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


class CaseThemeApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

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


class CaseThemeReasonApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

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


class CaseListApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

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

    def test_pagination(self):
        QUANTITY = 100
        PAGE_SIZE = 50
        STARTING_PAGE = 1
        NEXT_PAGE = 2
        baker.make(Case, _quantity=QUANTITY)
        url = reverse("cases-list")

        def get_paginated_results(PAGE_SIZE, PAGE=STARTING_PAGE):
            params = {"page_size": PAGE_SIZE, "page": PAGE}
            client = get_authenticated_client()
            response = client.get(url, params)

            return response.data["results"]

        self.assertNotEqual(
            get_paginated_results(PAGE_SIZE, STARTING_PAGE),
            get_paginated_results(PAGE_SIZE, NEXT_PAGE),
        )
        self.assertEqual(
            len(get_paginated_results(PAGE_SIZE)), len(get_paginated_results(PAGE_SIZE))
        )

    def test_filter_start_date(self):
        # Should only returb dates on the given date and newer
        DATE_A = datetime.datetime.now()
        DATE_B = DATE_A - datetime.timedelta(days=2)
        DATE_C = DATE_A + datetime.timedelta(days=2)

        FILTER_PARAMETERS = {"from_start_date": DATE_A.strftime("%Y-%m-%d")}

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

        FILTER_PARAMETERS = {"start_date": DATE_A.strftime("%Y-%m-%d")}

        baker.make(Case, start_date=DATE_A)
        baker.make(Case, start_date=DATE_B)
        baker.make(Case, start_date=DATE_C)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_open_cases(self):
        FILTER_PARAMETERS = {"open_cases": "true"}
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
        FILTER_PARAMETERS = {"open_cases": "false"}
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

    def test_filter_status(self):
        """
        Should return only one case
        """
        state_type_a = baker.make(CaseStateType)
        state_type_b = baker.make(CaseStateType)
        THEME_A = "thame_a"
        theme_a = baker.make(CaseTheme, name=THEME_A)
        case = baker.make(Case, theme=theme_a)
        baker.make(CaseWorkflow, case_state_type=state_type_a, case=case)
        baker.make(CaseWorkflow, case_state_type=state_type_b, case=case)

        url = reverse("cases-list")
        client = get_authenticated_client()

        FILTER_PARAMETERS = {"state_types": state_type_a.id}
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_status_different_states(self):
        """Each case has a different state type, should only return one case"""
        state_type_a = baker.make(CaseStateType)
        THEME_A = "thame_a"
        theme_a = baker.make(CaseTheme, name=THEME_A)
        case = baker.make(Case, theme=theme_a)
        case_workflow = baker.make(
            CaseWorkflow,
            id=42,
            created=datetime.datetime.now(),
            case=case,
            _quantity=10,
            case_state_type=state_type_a,
        )

        url = reverse("cases-list")
        client = get_authenticated_client()

        test_state = case_workflow[0]
        FILTER_PARAMETERS = {"state_types": test_state.case_state_type.id}
        response = client.get(url, FILTER_PARAMETERS)

        results = response.data["results"]
        self.assertEqual(len(results), 1)


class CaseCreatApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

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
                "theme_id": theme.pk,
                "reason_id": reason.pk,
                "bag_id": "foo bag ID",
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Case.objects.count(), 1)

    def test_authenticated_post_create_with_advertisements(self):
        self.assertEquals(Case.objects.count(), 0)

        theme = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme_id": theme.pk,
                "reason_id": reason.pk,
                "bag_id": "foo bag ID",
                "citizen_reports": [
                    {
                        "identification": 42,
                        "advertisements": [{"link": "https://www.example1.com"}],
                    }
                ],
                "advertisements": [{"link": "https://www.example2.com"}],
            },
            format="json",
        )
        cases = Case.objects.all()
        citizen_reports = CitizenReport.objects.all()
        advertisements = Advertisement.objects.all()
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(advertisements.count(), 2)
        self.assertEquals(cases.count(), 1)
        self.assertEquals(citizen_reports.count(), 1)
        self.assertEquals(cases[0].advertisements.count(), 2)
        self.assertEquals(cases[0].case_created_advertisements.count(), 1)
        self.assertEquals(citizen_reports[0].related_advertisements.count(), 1)

    def test_authenticated_post_create_fail_wrong_theme(self):
        """Should not be able to create a case if a wrong theme ID is given"""
        theme = baker.make(CaseTheme)
        reason = baker.make(CaseReason, theme=theme)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "theme_id": 10,
                "reason_id": reason.pk,
                "bag_id": "foo bag ID",
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)

    def test_authenticated_post_create_fail_wrong_reason(self):
        """Should not be able to create a case if a wrong theme ID is given"""
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
        """Request should fail if the CaseReason is not one of the given themes CaseReasons"""
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
                "theme_id": theme_b.pk,
                "reason_id": reason.pk,
                "bag_id": "foo bag ID",
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
                "theme_id": theme.pk,
                "reason_id": reason.pk,
                "bag_id": "foo bag ID",
            },
            format="json",
        )

        test_user = get_test_user()
        print("test_authenticated_post_create_author")
        print(response.data)
        case = Case.objects.get(id=response.data["id"])

        self.assertEquals(case.author, test_user)


class CaseThemeSummonTypeApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

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
