import uuid

from apps.users.user_manager import UserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from .utils import generate_username


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
    REQUIRED_FIELDS = []

    objects = UserManager()

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
            full_name = "".join(full_name)

            return full_name

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.username = generate_username(self.email)
        super().save(*args, **kwargs)


class SupportContact(models.Model):
    """
    Name and phonenumber that users can call if they need support
    Needs to be a model so that it can be edited in the django admin
    """

    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=25)

    def __str__(self):
        return f"Contact {self.name} - {self.phone_number}"
