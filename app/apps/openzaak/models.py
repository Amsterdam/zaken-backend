import json

from django.db import models


class Notification(models.Model):
    data = models.JSONField()
    processed = models.BooleanField(default=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ZaakType(models.Model):
    omschrijving = models.CharField(max_length=80, default="")
    url = models.URLField()
    active = models.BooleanField(default=True)


class DocumentType(models.Model):
    omschrijving = models.CharField(max_length=80, default="")
    url = models.URLField()
    active = models.BooleanField(default=True)
