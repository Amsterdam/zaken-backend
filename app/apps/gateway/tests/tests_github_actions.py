"""
A simple test for ensuring Github Action POC runs
"""
from django.test import TestCase


class GithubActionsTest(TestCase):
    def test_for_github_action(self):
        self.assertEqual(True, True)

    def test_for_github_action_fail(self):
        # Tests
        self.assertEqual(True, False)
