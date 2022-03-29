from apps.addresses.models import Address
from django.core import management
from django.test import TestCase
from model_bakery import baker

# TODO: Expand this by mocking the BAG API


class AddressModelTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_can_create_address(self):
        """Tests CaseStateType object creation"""
        self.assertEquals(Address.objects.count(), 0)

        baker.make(Address)

        self.assertEquals(Address.objects.count(), 1)
