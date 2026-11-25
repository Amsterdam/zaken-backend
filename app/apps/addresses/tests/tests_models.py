from unittest.mock import patch

from apps.addresses.mock import (
    mock_do_bag_search_pdok_by_bag_id_result,
    mock_get_bag_identificatie_and_stadsdeel_result,
    mock_get_bag_identificatie_and_stadsdeel_result_without_stadsdeel,
)
from apps.addresses.models import Address, District
from django.core import management
from django.test import TestCase
from model_bakery import baker

# TODO: Expand this by mocking the BAG API


class AddressModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_address(self):
        """Tests Address object creation without bag mocks"""
        self.assertEqual(Address.objects.count(), 0)
        baker.make(Address)
        self.assertEqual(Address.objects.count(), 1)

    @patch("apps.addresses.models.do_bag_search_benkagg_by_id")
    @patch("apps.addresses.models.do_bag_search_pdok_by_bag_id")
    def test_can_create_address_with_bag_result_without_stadsdeel(
        self, mock_do_bag_search_pdok_by_bag_id, mock_do_bag_search_benkagg_id
    ):
        """Tests Address object creation with bag data mocks without stadsdeel entry"""

        mock_do_bag_search_pdok_by_bag_id.return_value = (
            mock_do_bag_search_pdok_by_bag_id_result()
        )
        mock_do_bag_search_benkagg_id.return_value = (
            mock_get_bag_identificatie_and_stadsdeel_result_without_stadsdeel()
        )

        self.assertEqual(Address.objects.count(), 0)
        self.assertEqual(District.objects.count(), 0)

        baker.make(Address)

        mock_do_bag_search_pdok_by_bag_id.assert_called()
        mock_do_bag_search_benkagg_id.assert_called()

        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(District.objects.count(), 0)

    @patch("apps.addresses.models.do_bag_search_benkagg_by_id")
    @patch("apps.addresses.models.do_bag_search_pdok_by_bag_id")
    def test_can_create_address_with_bag_result(
        self, mock_do_bag_search_pdok_by_bag_id, mock_do_bag_search_benkagg_id
    ):
        """Tests Address object creation with bag data mocks"""

        mock_do_bag_search_pdok_by_bag_id.return_value = (
            mock_do_bag_search_pdok_by_bag_id_result()
        )
        mock_do_bag_search_benkagg_id.return_value = (
            mock_get_bag_identificatie_and_stadsdeel_result()
        )

        self.assertEqual(Address.objects.count(), 0)
        self.assertEqual(District.objects.count(), 0)

        address = baker.make(Address)

        mock_do_bag_search_pdok_by_bag_id.assert_called()
        mock_do_bag_search_benkagg_id.assert_called()

        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(District.objects.count(), 1)

        self.assertEqual(address.district.name, "Zuidoost")
        self.assertEqual(address.city, "Amsterdam")


class AddressCityMigrationTest(TestCase):
    def get_city(self, bag_id, postal_code):
        from importlib import import_module

        migration = import_module("apps.addresses.migrations.0008_address_city")
        return migration.get_city(Address(bag_id=bag_id, postal_code=postal_code))

    def test_weesp_by_postal_code(self):
        self.assertEqual(self.get_city("0363010012581207", "1384CC"), "Weesp")

    def test_weesp_by_former_municipality_bag_id(self):
        self.assertEqual(self.get_city("0457010000059188", None), "Weesp")
        self.assertEqual(self.get_city("0424010000009449", ""), "Weesp")

    def test_amsterdam(self):
        self.assertEqual(self.get_city("0363010000802188", "1011KM"), "Amsterdam")

    def test_unknown_without_postal_code(self):
        self.assertIsNone(self.get_city("0363010012598484", None))


class AddressFullAddressTest(TestCase):
    def full_address(self, **kwargs):
        defaults = {
            "street_name": "Foppingadreef",
            "number": 26,
            "suffix_letter": None,
            "suffix": None,
            "postal_code": "1102CX",
            "city": "Amsterdam",
        }
        return Address(**{**defaults, **kwargs}).full_address

    def test_suffix_letter_and_suffix(self):
        self.assertEqual(
            self.full_address(suffix_letter="A", suffix="1"),
            "Foppingadreef 26A-1, 1102CX Amsterdam",
        )

    def test_suffix_letter_only(self):
        self.assertEqual(
            self.full_address(suffix_letter="A"), "Foppingadreef 26A, 1102CX Amsterdam"
        )

    def test_suffix_only(self):
        self.assertEqual(
            self.full_address(suffix="1"), "Foppingadreef 26-1, 1102CX Amsterdam"
        )

    def test_without_city(self):
        self.assertEqual(self.full_address(city=None), "Foppingadreef 26, 1102CX")

    def test_street_name_with_abbreviation(self):
        self.assertEqual(
            self.full_address(
                street_name="tt. Vasumweg",
                number=32,
                suffix_letter="K",
                suffix="6",
                postal_code="1033SC",
            ),
            "tt. Vasumweg 32K-6, 1033SC Amsterdam",
        )
