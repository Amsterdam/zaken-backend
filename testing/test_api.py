import logging
import os
import unittest

from api import API
from themes import vakantieverhuur  # , nogiets

host = os.environ.get("API_HOST", "http://localhost:8080/api/v1")
loglevel = os.environ.get("LOGLEVEL", "WARNING")

logging.basicConfig(level=loglevel)


class TestVisitFlow(unittest.TestCase):
    def setUp(self):
        self.api = API(host)

    def test_flows(self):
        all_suites = [
            vakantieverhuur.get_suite(self.api),
            # nogiets.flows
        ]
        for theme_suite in all_suites:
            for flow in theme_suite:
                case = flow.run(self.api)
                open_tasks = self.api.get_tasks_for_case_id(case["id"])
                self.assertEqual(len(open_tasks), 0)


if __name__ == "__main__":
    unittest.main()
