import logging

from apps.addresses.models import Address, District, HousingCorporation
from apps.addresses.serializers import (
    AddressSerializer,
    DistrictSerializer,
    HousingCorporationSerializer,
    ResidentsSerializer,
)
from apps.cases.models import Advertisement
from apps.cases.serializers import AdvertisementSerializer, CaseSerializer
from apps.permits.mixins import PermitDetailsMixin
from apps.users import permissions
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from utils.api_queries_brp import get_brp_by_nummeraanduiding_id

logger = logging.getLogger(__name__)

OPEN_CASES_QUERY_PARAMETER = "open_cases"
open_cases = OpenApiParameter(
    name=OPEN_CASES_QUERY_PARAMETER,
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Open Cases",
)


class AddressViewSet(ViewSet, GenericAPIView, PermitDetailsMixin):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    lookup_field = "bag_id"

    @action(
        detail=True,
        methods=["get"],
        serializer_class=ResidentsSerializer,
        url_path="residents",
        permission_classes=[permissions.CanAccessBRP],
    )
    def residents_by_bag_id(self, request, bag_id):
        # Get address
        try:
            address = Address.objects.get(bag_id=bag_id)
        except Address.DoesNotExist:
            address = Address(bag_id=bag_id)

        # If no nummeraanduiding_id, get it!
        if not address.nummeraanduiding_id:
            try:
                address.get_bag_address_data()
                address.get_bag_nummeraanduiding_id()
            except Exception:
                return Response(
                    {"error": "Bag data could not be obtained"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # nummeraanduiding_id should have been retrieved, so get BRP data
        if address.nummeraanduiding_id:
            try:
                brp_data, status_code = get_brp_by_nummeraanduiding_id(
                    request, address.nummeraanduiding_id
                )
                serialized_residents = ResidentsSerializer(data=brp_data)
                serialized_residents.is_valid(raise_exception=True)
                return Response(serialized_residents.data, status=status_code)
            except Exception:
                return Response(
                    {"error": "BRP data could not be obtained"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"error": "no nummeraanduiding_id found"}, status=status.HTTP_404_NOT_FOUND
        )

    @extend_schema(
        parameters=[open_cases],
        description="Get cases for given BAG ID",
        responses={200: CaseSerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["get"],
        serializer_class=CaseSerializer,
        url_path="cases",
    )
    def cases(self, request, bag_id, **kwargs):
        try:
            address = Address.objects.get(bag_id=bag_id)
        except Address.DoesNotExist:
            return Response({"results": []})

        try:
            open_cases = request.GET.get(OPEN_CASES_QUERY_PARAMETER, None)

            if open_cases is None:
                query_set = address.cases.all()
            elif open_cases == "true":
                query_set = address.cases.filter(end_date__isnull=True)
            else:
                query_set = address.cases.filter(end_date__isnull=False)

            paginator = LimitOffsetPagination()
            context = paginator.paginate_queryset(query_set, request)
            serializer = CaseSerializer(context, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f"Could not retrieve cases for bag id {bag_id}: {e}")

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Gets the Advertisements associated with this address",
        responses={status.HTTP_200_OK: AdvertisementSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="advertisements",
        methods=["get"],
    )
    def advertisements(self, request, bag_id):
        paginator = LimitOffsetPagination()
        address = self.get_object()
        query_set = Advertisement.objects.filter(
            case__address=address,
        )
        context = paginator.paginate_queryset(query_set, request)
        serializer = AdvertisementSerializer(context, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets all housing corporations",
        responses={status.HTTP_200_OK: HousingCorporationSerializer(many=True)},
    )
    @action(
        detail=False,
        url_path="housing-corporations",
        methods=["get"],
    )
    def housing_corporations(self, request):
        paginator = LimitOffsetPagination()
        queryset = HousingCorporation.objects.all()
        context = paginator.paginate_queryset(queryset, request)
        serializer = HousingCorporationSerializer(context, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets all districts",
        responses={status.HTTP_200_OK: DistrictSerializer(many=True)},
    )
    @action(
        detail=False,
        url_path="districts",
        methods=["get"],
    )
    def districts(self, request):
        paginator = LimitOffsetPagination()
        queryset = District.objects.all()
        context = paginator.paginate_queryset(queryset, request)
        serializer = DistrictSerializer(context, many=True)
        return paginator.get_paginated_response(serializer.data)
