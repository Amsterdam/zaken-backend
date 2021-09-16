import logging
import os
import unittest

from api import API
from themes import holiday_rental  # , anothertheme

host = os.environ.get("API_HOST", "http://localhost:8080/api/v1")
loglevel = os.environ.get("LOGLEVEL", "WARNING")

logging.basicConfig(level=loglevel)


class TestVisitFlow(unittest.TestCase):
    def setUp(self):
        self.api = API(host)

    def test_suites(self):
        themes = [
            holiday_rental,
            # anotherteam,
        ]
        for theme in themes:
            flows = theme.get_flows(self.api)
            for flow in flows:
                flow.run(self.api)


if __name__ == "__main__":
    unittest.main()
