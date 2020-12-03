from django.db import models


# Create your models here.
class SupportContact(models.Model):
    """
    Name and phonenumber that users can call if they need support
    Needs to be a model so that it can be edited in the django admin
    """

    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=25)
    email = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"Contact {self.name} - {self.title}"
