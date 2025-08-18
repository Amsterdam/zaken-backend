from apps.addresses.models import Address
from apps.addresses.utils import search
from django.core import management
from django.test import TestCase
from model_bakery import baker


class AdressUtilsSearchTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_no_results(self):
        results = search()
        self.assertEqual(len(results), 0)

    def test_no_matching_street_name(self):
        baker.make(Address, street_name="Foo")

        results = search(street_name="Warmoesstraat")
        self.assertEqual(len(results), 0)

    def test_matching_street_name(self):
        STREET_NAME = "Warmoesstraat"
        address = baker.make(Address, street_name=STREET_NAME)

        results = search(street_name=STREET_NAME)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_similar_street_name(self):
        STREET_NAME = "Warmoesstraat"
        SIMILAR_STREET_NAME = "Warmosstraat"
        address = baker.make(Address, street_name=STREET_NAME)

        results = search(street_name=SIMILAR_STREET_NAME)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_multiple_similar_street_name(self):
        SIMILAR_STREET_NAMES = [
            "Warmosstraat",
            "Warmoesstrat",
            "Wamoesstraat",
            "Warmoestraat",
            "Warmeostraat",
            "aarmoestraat",
            "Warmoestraat",
        ]
        OTHER_STREET_NAMES = [
            "Elleboogsteeg",
            "Waterpoortsteeg",
            "Kogge­straat",
            "Ramskooi",
        ]

        STREET_NAMES = SIMILAR_STREET_NAMES + OTHER_STREET_NAMES

        for street_name in STREET_NAMES:
            baker.make(Address, street_name=street_name)

        results = search(street_name="Warmoesstraat")
        self.assertEqual(len(results), len(SIMILAR_STREET_NAMES))

    def test_matching_street_name_number(self):
        STREET_NAME = "Warmoesstraat"
        address = baker.make(Address, street_name=STREET_NAME, number=1)
        baker.make(Address, street_name=STREET_NAME, number=2)
        baker.make(Address, street_name=STREET_NAME, number=11)

        results = search(street_name=STREET_NAME, number=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_matching_street_name_numer(self):
        STREET_NAME = "Warmoesstraat"
        address = baker.make(Address, street_name=STREET_NAME, number=1, suffix="A")
        baker.make(Address, street_name=STREET_NAME, number=2, suffix="A")
        baker.make(Address, street_name=STREET_NAME, number=11, suffix="A")

        results = search(street_name=STREET_NAME, number=1, suffix="A")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_no_matching_postal_code(self):
        baker.make(Address, postal_code="1012GW")

        results = search(postal_code="Foo")
        self.assertEqual(len(results), 0)

    def test_matching_postal_code(self):
        POSTAL_CODE = "1012GW"
        address = baker.make(Address, postal_code=POSTAL_CODE)

        results = search(postal_code=POSTAL_CODE)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_matching_postal_code_leading_space(self):
        POSTAL_CODE = "1012GW"
        address = baker.make(Address, postal_code=POSTAL_CODE)

        results = search(postal_code=" " + POSTAL_CODE)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_matching_postal_code_trailing_space(self):
        POSTAL_CODE = "1012GW"
        address = baker.make(Address, postal_code=POSTAL_CODE)

        results = search(postal_code=POSTAL_CODE + " ")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_matching_postal_code_mid_space(self):
        POSTAL_CODE_CORRECT = "1012GW"
        POSTAL_CODE_SPACE = "1012 GW"
        address = baker.make(Address, postal_code=POSTAL_CODE_CORRECT)

        results = search(postal_code=POSTAL_CODE_SPACE)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_matching_postal_code_number(self):
        POSTAL_CODE = "1012GW"
        address = baker.make(Address, postal_code=POSTAL_CODE, number=1)
        baker.make(Address, postal_code=POSTAL_CODE, number=2)
        baker.make(Address, postal_code=POSTAL_CODE, number=3)

        results = search(postal_code=POSTAL_CODE, number=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)

    def test_matching_postal_code_number_suffix(self):
        POSTAL_CODE = "1012GW"
        SUFFIX = "A"

        address = baker.make(Address, postal_code=POSTAL_CODE, number=1, suffix=SUFFIX)
        baker.make(Address, postal_code=POSTAL_CODE, number=2, suffix=SUFFIX)
        baker.make(Address, postal_code=POSTAL_CODE, number=3, suffix=SUFFIX)

        results = search(postal_code=POSTAL_CODE, number=1, suffix=SUFFIX)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], address)
