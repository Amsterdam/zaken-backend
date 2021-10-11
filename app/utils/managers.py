from django.db import models
from django.db.models.signals import post_save, pre_save


class BulkCreateSignalsManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        for i in objs:
            pre_save.send(i.__class__, instance=i)
        a = super().bulk_create(objs, **kwargs)
        for i in objs:
            post_save.send(i.__class__, instance=i, created=True)
        return a
