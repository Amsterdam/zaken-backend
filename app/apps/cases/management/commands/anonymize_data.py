import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from utils.anonymizer import ANONYMIZER_ENV_BLACKLIST, get_default_anonymizer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):

        if settings.ENVIRONMENT in ANONYMIZER_ENV_BLACKLIST:
            raise Exception(
                f"Wrong enviroment: The env {settings.ENVIRONMENT} does not allow anonyzation"
            )

        anonymizer = get_default_anonymizer()
        anonymizer.perform_update()
