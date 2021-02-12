import logging
from datetime import datetime

from apps.addresses.models import Address
from apps.cases.const import IN_PROGRESS
from apps.cases.models import Case
from apps.cases.serializers import CaseSerializer
from apps.fines.legacy_const import STADIA_WITH_FINES
from apps.fines.models import Fine
from apps.gateway.push.serializers import PushSerializer
from apps.users.auth_apps import TopKeyAuth
from django.contrib.auth import get_user_model
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

LOGGER = logging.getLogger(__name__)


class PushViewSet(viewsets.ViewSet):
    """
    Populates data through a push from Top, after which a new state is created.
    A push from Top occurs when a case is added to an itinerary.
    After migrating from BWV to Zaken we can remove most of this push, and Top can do a simpler (and more generic) CREATE request for adding a state.
    """

    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = PushSerializer

    def create(self, request):
        LOGGER.info("Receiving pushed case")
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            LOGGER.error("Serializer error: {serializer.errors}")
            raise APIException(f"Serializer error: {serializer.errors}")

        try:
            identification = data.get("identification")
            case_type = data.get("case_type")
            bag_id = data.get("bag_id")
            start_date = data.get("start_date")
            end_date = data.get("end_date", None)
            users = data.get("users", [])
            states_data = data.get("states", [])

            case = self.create_case(
                identification, case_type, bag_id, start_date, end_date
            )
            self.create_fines(states_data, case)
            users = self.create_users(users)

            return Response(
                {
                    "case": CaseSerializer(case).data,
                }
            )

        except Exception as e:
            LOGGER.error(f"Could not process push data: {e}")
            raise APIException(f"Could not push data: {e}")

    def create_case(self, identification, case_type, bag_id, start_date, end_date):
        case, _ = Case.objects.get_or_create(identification=identification)
        address = Address.get(bag_id)

        case.start_date = start_date
        case.end_date = end_date
        case.address = address
        case.is_legacy_bwv = True
        case.save()

        return case

    def create_fines(self, states_data, case):
        """
        Creates Fine objects based on legacy stadia
        """
        fines = []
        for state_data in states_data:
            name = state_data.get("name")
            invoice_identification = state_data.get("invoice_identification")

            if name in STADIA_WITH_FINES:
                fine, _ = Fine.objects.get_or_create(
                    identification=invoice_identification, case=case
                )

                fines.append(fine)

        return fines

    def create_users(self, user_emails):
        users = []
        user_model = get_user_model()

        for user_email in user_emails:
            user, _ = user_model.objects.get_or_create(email=user_email)
            users.append(user)

        return users
