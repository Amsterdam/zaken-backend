import time

from apps.cases.models import Case
from config.celery import app as celery_app


@celery_app.task
def do_some_queries():
    time.sleep(10)
    return Case.objects.count()


@celery_app.task
def query_every_five_mins():
    return Case.objects.count()
