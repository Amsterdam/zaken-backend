from unittest.mock import patch

from apps.addresses.mock import (
    mock_do_bag_search_id_result,
    mock_do_bag_search_id_result_without_links,
    mock_get_bag_data_result,
    mock_get_bag_data_result_without_stadsdeel,
)
from apps.addresses.models import Address, District
from django.core import management
from django.test import TestCase
from model_bakery import baker
from utils.exceptions import DistrictNotFoundError

# TODO: Expand this by mocking the BAG API


class AddressModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_address(self):
        """Tests Address object creation without bag mocks"""
        self.assertEquals(Address.objects.count(), 0)

        baker.make(Address)

        self.assertEquals(Address.objects.count(), 1)

    @patch("apps.addresses.models.get_bag_data")
    @patch("apps.addresses.models.do_bag_search_id")
    def test_can_create_address_with_bag_result_without_verblijftobject_url(
        self, mock_do_bag_search_id, mock_get_bag_data
    ):
        """Tests Address object creation with bag data mocks without verblijftobject url"""

        mock_do_bag_search_id.return_value = (
            mock_do_bag_search_id_result_without_links()
        )
        mock_get_bag_data.return_value = mock_get_bag_data_result()

        self.assertEquals(Address.objects.count(), 0)
        self.assertEquals(District.objects.count(), 0)

        with self.assertRaises(DistrictNotFoundError):
            baker.make(Address)
        mock_do_bag_search_id.assert_called()

    @patch("apps.addresses.models.get_bag_data")
    @patch("apps.addresses.models.do_bag_search_id")
    def test_can_create_address_with_bag_result_without_verblijftobject_stadsdeel(
        self, mock_do_bag_search_id, mock_get_bag_data
    ):
        """Tests Address object creation with bag data mocks without verblijftobject stadsdeel entry"""

        mock_do_bag_search_id.return_value = mock_do_bag_search_id_result()
        mock_get_bag_data.return_value = mock_get_bag_data_result_without_stadsdeel()

        self.assertEquals(Address.objects.count(), 0)
        self.assertEquals(District.objects.count(), 0)

        with self.assertRaises(DistrictNotFoundError):
            baker.make(Address)
        mock_do_bag_search_id.assert_called()
        mock_get_bag_data.assert_called_with(
            "https://api.data.amsterdam.nl/bag/v1.1/verblijfsobject/0363010001028805/"
        )

    @patch("apps.addresses.models.get_bag_data")
    @patch("apps.addresses.models.do_bag_search_id")
    def test_can_create_address_with_bag_result(
        self, mock_do_bag_search_id, mock_get_bag_data
    ):
        """Tests Address object creation with bag data mocks"""

        mock_do_bag_search_id.return_value = mock_do_bag_search_id_result()
        mock_get_bag_data.return_value = mock_get_bag_data_result()

        self.assertEquals(Address.objects.count(), 0)
        self.assertEquals(District.objects.count(), 0)

        baker.make(Address)

        mock_do_bag_search_id.assert_called()
        mock_get_bag_data.assert_called_with(
            "https://api.data.amsterdam.nl/bag/v1.1/verblijfsobject/0363010001028805/"
        )

        self.assertEquals(Address.objects.count(), 1)
        self.assertEquals(District.objects.count(), 1)
