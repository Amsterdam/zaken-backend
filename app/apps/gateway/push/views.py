import logging

from apps.cases.models import Address, Case, CaseType, OpenZaakState, OpenZaakStateType
from apps.cases.serializers import CaseSerializer, OpenZaakStateSerializer
from apps.gateway.push.serializers import PushSerializer
from apps.users.auth_apps import TopKeyAuth
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

LOGGER = logging.getLogger(__name__)


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

            case, created = Case.objects.get_or_create(identification=identification)
            case_type = CaseType.get(case_type)
            address = Address.get(bag_id)

            case.start_date = start_date
            case.end_date = end_date
            case.case_type = case_type
            case.address = address
            case.save()

            states_data = data.get("states")
            states = []
            for state_data in states_data:
                name = state_data.get("name")
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

            return Response(
                {
                    "case": CaseSerializer(case).data,
                    "states": OpenZaakStateSerializer(states, many=True).data,
                }
            )

        except Exception as e:
            LOGGER.error(f"Could not process push data: {e}")
            raise APIException(f"Could not push data: {e}")
