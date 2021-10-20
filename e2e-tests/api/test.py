import logging
import unittest

from api.config import api_config
from api.mock import get_case_mock

logger = logging.getLogger("api")


class DefaultAPITest(unittest.TestCase):
    def setUp(self):
        from api.client import Client

        self.client = Client(api_config)

    def get_case(self):
        case_data = self.get_case_data()
        case_mock = get_case_mock(**case_data)
        return self.client.create_case(case_mock)

    def get_case_data(self):
        return {}
