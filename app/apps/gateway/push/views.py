from apps.cases.models import Address, Case, CaseType
from apps.cases.serializers import CaseSerializer
from apps.gateway.push.serializers import PushCheckActionSerializer, PushSerializer
from apps.users.auth_apps import TopKeyAuth
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class PushCheckActionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated | TopKeyAuth]
    serializer_class = PushCheckActionSerializer

    def create(self, request):
        data = request.data
        print(f"POST Create CHECK actions {data}")
        # format: {'identification': 'foo_id', 'check_action': True}
        # TODO: Should do something with this format
        return Response({})


class PushViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated | TopKeyAuth]
    serializer_class = PushSerializer

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            print(f"Serializer error: {serializer.errors}")
            raise APIException(f"Serializer error: {serializer.errors}")

        try:
            identification = data.get("identification")
            case_type = data.get("case_type")
            bag_id = data.get("bag_id")
            start_date = data.get("start_date")
            end_date = data.get("end_date", None)

            case = Case.get(identification)
            case_type = CaseType.get(case_type)
            address = Address.get(bag_id)

            case.start_date = start_date
            case.end_date = end_date
            case.case_type = case_type
            case.address = address
            case.save()

            return Response({"case": CaseSerializer(case).data})

        except Exception as e:
            raise APIException(f"Could not get or create case: {e}")
