import json
import logging
from collections import namedtuple
from datetime import timedelta

from apps.cases.models import Case, CaseDocument, CaseState, CaseTheme
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...helpers import (
    get_document,
    get_open_zaak_case,
    get_open_zaak_case_document_connection,
    get_open_zaak_case_state,
)
from ...models import Notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Handle the notifications that were send via open notifications"

    def process_case(self, notification, case_theme, action, resource_url):
        # Resource should be a case
        existing_case = Case.objects.filter(case_url=resource_url).first()
        if action == "update" and existing_case:
            case_data = get_open_zaak_case(resource_url)
            existing_case.description = case_data.toelichting
            existing_case.start_date = case_data.startdatum
            existing_case.end_date = case_data.einddatum
            existing_case.save()

        if action == "destroy" and existing_case:
            existing_case.deletedcase_deleted = True
            existing_case.save()

        self.set_processed(notification)

    def process_status(self, notification, action, resource_url, hoofd_object):
        # Resource should be a case
        case = Case.objects.filter(case_url=hoofd_object).first()
        if not case:
            return self.set_processed(
                notification
            )  # Stopping cause we don't know the case
        if action == "create":
            status = get_open_zaak_case_state(resource_url)
            if status.statustype == settings.OPENZAAK_CASETYPEURL_HANDHAVING:
                state = CaseState.CaseStateChoice.HANDHAVING
            elif status.statustype == settings.OPENZAAK_CASETYPEURL_AFGESLOTEN:
                state = CaseState.CaseStateChoice.AFGESLOTEN
            elif status.statustype == settings.OPENZAAK_CASETYPEURL_TOEZICHT:
                state = CaseState.CaseStateChoice.TOEZICHT
            else:
                return self.set_processed(notification)

            CaseState.objects.create(
                case=case,
                status=state,
                created=status.datum_status_gezet,
                system_build=True,
            )
        return self.set_processed(
            notification
        )  # Stopping cause we don't know the state type

    def process_case_document(self, notification, action, resource_url, hoofd_object):
        case = Case.objects.filter(case_url=hoofd_object).first()

        if not case:
            return self.set_processed(
                notification
            )  # Stopping cause we don't know the case

        if action == "create":
            zaakinformatieobject = get_open_zaak_case_document_connection(resource_url)
            document_url = zaakinformatieobject.get("informatieobject")

            case_document = CaseDocument.objects.filter(
                case=case, document_url=document_url
            ).first()
            if case_document:
                case_document.connected = True
                case_document.save()
            else:
                document = get_document(document_url)
                CaseDocument.objects.create(
                    case=case,
                    document_url=document_url,
                    document_content=document.inhoud,
                    connected=True,
                )
        self.set_processed(notification)

    def process_case_channel(self, data, notification):
        zaak_type = data.kenmerken.get("zaaktype")
        action = data.actie
        resource = data.resource
        resource_url = data.resourceUrl
        hoofd_object = data.hoofdObject

        case_theme = CaseTheme.objects.filter(case_type_url=zaak_type).first()
        if not case_theme:
            return self.set_processed(notification=notification)

        if resource == "zaak":
            return self.process_case(notification, case_theme, action, resource_url)
        if resource == "status":
            return self.process_status(notification, action, resource_url, hoofd_object)
        if resource == "zaakinformatieobject":
            return self.process_case_document(
                notification, action, resource_url, hoofd_object
            )
        assert False, "Nothing to process"

    def set_processed(self, notification):
        notification.processed = True
        notification.save()

    def proccess_notification(self, notification):
        data = notification.data
        if isinstance(data, str):
            data = json.loads(data)
        object_data = namedtuple("NotificationData", data.keys())(*data.values())

        if object_data.kanaal == "zaken":
            return self.process_case_channel(object_data, notification)
        self.set_processed(notification)

    def handle(self, *args, **options):
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        notifications = Notification.objects.filter(
            processed=False, created_at__lt=one_minute_ago
        )
        for notification in notifications:
            try:
                self.proccess_notification(notification=notification)
            except Exception as e:
                # Catch all errors to make sure that if a notification fails, it will not halt all
                # notifications from being processed.
                logger.exception(e)
