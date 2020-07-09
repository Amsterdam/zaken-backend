"""
A simple test for ensuring Github Action POC runs
"""
from django.test import TestCase


class GithubActionsTest(TestCase):
    def dummy_test_for_github_actions(self):
        self.assertEqual(True, True)

    def dummy_test_fail_for_github_actions(self):
        self.assertEqual(True, False)
