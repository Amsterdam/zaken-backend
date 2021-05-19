from unittest.mock import patch

from apps.permits.mocks import (
    get_decos_join_mock_folder_fields,
    get_decos_join_mock_object_fields,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_unauthenticated_client,
)


class PermitViewSetTest(APITestCase):
    """
    Tests for the API endpoints for retrieving permit data
    """

    MOCK_BAG_ID = "0363010000809805"
    PERMIT_URL_NAME = "addresses-permit details"

    def _get_url(self):
        return "%s" % (reverse(self.PERMIT_URL_NAME, args=[self.MOCK_BAG_ID]),)

    def test_unauthenticated_request(self):
        """
        An unauthenticated request should not be possible
        """

        url = self._get_url()
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "apps.permits.api_queries_decos_join.DecosJoinRequest.get_decos_object_with_bag_id"
    )
    @patch("apps.permits.api_queries_decos_join.DecosJoinRequest._get_decos_folder")
    def test_authenticated_requests_succeeds(
        self, mock__get_decos_folder, mock_get_decos_object_with_bag_id
    ):
        """
        An authenticated request succeeds and contains all the necessary data
        """

        mock_get_decos_object_with_bag_id.return_value = (
            get_decos_join_mock_object_fields()
        )
        mock__get_decos_folder.return_value = get_decos_join_mock_folder_fields()

        url = self._get_url()
        client = get_authenticated_client()
        response = client.get(url)

        # The response returns a 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # self.assertEquals(response.json(), MOCK_RESPONSE)
