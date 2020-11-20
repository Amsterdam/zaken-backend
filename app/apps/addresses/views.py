import logging

from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer, ResidentsSerializer
from apps.permits.mixins import PermitCheckmarkMixin, PermitDetailsMixin
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from utils.api_queries_brp import get_brp

logger = logging.getLogger(__name__)


class AddressViewSet(ViewSet, PermitCheckmarkMixin, PermitDetailsMixin):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    lookup_field = "bag_id"

    @action(
        detail=True,
        methods=["get"],
        serializer_class=ResidentsSerializer,
        url_path="residents",
    )
    def residents_by_bag_id(self, request, bag_id):
        try:
            brp_data = get_brp(bag_id)
            serialized_residents = ResidentsSerializer(data=brp_data)
            serialized_residents.is_valid()

            return Response(serialized_residents.data)

        except Exception as e:
            logger.error(f"Could not retrieve residents for bag id {bag_id}: {e}")

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
