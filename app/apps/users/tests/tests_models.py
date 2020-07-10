"""
Tests for cases models
"""
from apps.users.models import User
from django.db import transaction
from django.test import TestCase

USER_EMAIL = "foo@foo.com"


class UserModelTest(TestCase):
    def test_create_user(self):
        """
        A User can be created
        """
        self.assertEqual(User.objects.count(), 0)
        User.objects.create(email=USER_EMAIL)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_existing_email(self):
        """
        A User cannot be created if another User has the same email
        """
        self.assertEqual(User.objects.count(), 0)
        User.objects.create(email=USER_EMAIL)

        with transaction.atomic():
            with self.assertRaises(Exception):
                User.objects.create(email=USER_EMAIL)

        self.assertEqual(User.objects.count(), 1)

    def test_create_multiple_users(self):
        """
        Multiple users can be created as long as their emails differ
        """
        self.assertEqual(User.objects.count(), 0)
        User.objects.create(email=USER_EMAIL)
        User.objects.create(email="foo-other-email@foo.com")
        self.assertEqual(User.objects.count(), 2)

    def test_username(self):
        """
        A User's username is equal to it's email
        (with the exception of when the email is normalized to generate the username.
        This is tested in tests_util.py)
        """
        USER_EMAIL = "foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)

        self.assertEqual(user.username, USER_EMAIL)
        self.assertEqual(user.email, USER_EMAIL)

    def test_string_representation(self):
        """
        A User object is displayed as its parsed email
        """
        USER_EMAIL = "f.foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)

        self.assertEqual(user.__str__(), "F. Foo")

    def test_credentials(self):
        """
        A User does not have staff or superuser credentials
        """
        USER_EMAIL = "foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_full_name_normal(self):
        """
        A User's full_name is derived from its email
        """
        USER_EMAIL = "f.foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)
        self.assertEqual(user.full_name, "F. Foo")

    def test_full_name_double_initials(self):
        """
        A User's full_name with initials is derived from its email correctly
        """
        USER_EMAIL = "f.o.foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)
        self.assertEqual(user.full_name, "F.O. Foo")

    def test_full_name_double_surname(self):
        """
        A User's full_name with initials and double surname is derived from its email correctly
        """
        USER_EMAIL = "f.o.de.foo@foo.com"
        user = User.objects.create(email=USER_EMAIL)
        self.assertEqual(user.full_name, "F.O. De Foo")
