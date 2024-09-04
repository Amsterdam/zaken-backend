import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.base import Model

from .permissions import custom_permissions
from .utils import generate_username

if not hasattr(Group, "display_name"):
    display_name = models.CharField(
        max_length=40,
        blank=False,
    )
    display_name.contribute_to_class(Group, "display_name")


class Permission(Model):
    """
    Non-managed Permission class so we can do 'users.permission'.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = custom_permissions


class UserGroup(Group):
    class Meta:
        proxy = True


class User(AbstractUser):
    class Meta:
        ordering = ["email"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        blank=False,
        error_messages={"unique": "A user with that email already exists."},
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    @property
    def full_name(self):
        """
        Parses and returns last name from email (f.foo will return F. Foo)
        """

        def capitalize(string):
            return string.capitalize()

        def add_punctuation(string):
            return string + "." if len(string) == 1 else " " + string

        if self.email:
            full_name = self.email.split("@")[0].split(".")
            full_name = [capitalize(part) for part in full_name]
            full_name = [add_punctuation(part) for part in full_name]
            full_name = "".join(full_name).strip()

            return full_name

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.username = generate_username(self.email)
        super().save(*args, **kwargs)
