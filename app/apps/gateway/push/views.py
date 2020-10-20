import logging
from datetime import datetime

from apps.cases.const import IN_PROGRESS
from apps.cases.models import (
    Address,
    Case,
    CaseState,
    CaseStateType,
    CaseType,
    OpenZaakState,
    OpenZaakStateType,
)
from apps.cases.serializers import (
    CaseSerializer,
    CaseStateSerializer,
    OpenZaakStateSerializer,
)
from apps.gateway.push.serializers import PushSerializer
from apps.users.auth_apps import TopKeyAuth
from apps.users.models import User
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

LOGGER = logging.getLogger(__name__)


def create_case(identification, case_type, bag_id, start_date, end_date):
    case, _ = Case.objects.get_or_create(identification=identification)
    case_type = CaseType.get(case_type)
    address = Address.get(bag_id)

    case.start_date = start_date
    case.end_date = end_date
    case.case_type = case_type
    case.address = address
    case.save()

    return case


def create_legacy_states(states_data, case):
    states = []
    for state_data in states_data:
        name = state_data.get("name")

        # TODO: These should be renamed BWV instead of OpenZaak
        state_type = OpenZaakStateType.get(name)
        state, created = OpenZaakState.objects.get_or_create(
            state_type=state_type,
            case=case,
            invoice_identification=state_data.get("invoice_identification"),
        )

        state.start_date = state_data.get("start_date")
        state.end_date = state_data.get("end_date", None)
        state.gauge_date = state_data.get("gauge_date", None)
        state.save()

        states.append(state)

    return states


def create_users(user_emails):
    users = []

    for user_email in user_emails:
        user, _ = User.objects.get_or_create(email=user_email)
        users.append(user)

    return users


def create_state(case, users):
    case_state_type, _ = CaseStateType.objects.get_or_create(name=IN_PROGRESS)
    case_state, _ = CaseState.objects.get_or_create(
        case=case, status=case_state_type, state_date=datetime.now().date()
    )

    case_state.users.set(users)
    case_state.save()

    return case_state


class PushViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated | TopKeyAuth]
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

            case = create_case(identification, case_type, bag_id, start_date, end_date)
            legacy_states = create_legacy_states(states_data, case)
            users = create_users(users)
            state = create_state(case, users)

            return Response(
                {
                    "case": CaseSerializer(case).data,
                    "legacy_states": OpenZaakStateSerializer(
                        legacy_states, many=True
                    ).data,
                    "state": CaseStateSerializer(state).data,
                }
            )

        except Exception as e:
            LOGGER.error(f"Could not process push data: {e}")
            raise APIException(f"Could not push data: {e}")
