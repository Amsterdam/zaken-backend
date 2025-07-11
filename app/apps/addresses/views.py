import logging

from apps.addresses.models import Address, District, HousingCorporation
from apps.addresses.serializers import (
    AddressSerializer,
    BrpSerializer,
    DistrictSerializer,
    GetResidentsSerializer,
    HousingCorporationSerializer,
    MeldingenSerializer,
    RegistrationDetailsSerializer,
    RegistrationNumberSerializer,
    ResidentsSerializer,
)
from apps.cases.models import Advertisement
from apps.cases.serializers import AdvertisementSerializer, CaseSerializer
from apps.permits.mixins import PermitDetailsMixin
from apps.users import permissions
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from utils.api_queries_benk_brp import BrpRequest
from utils.api_queries_brp import get_brp_by_nummeraanduiding_id
from utils.api_queries_toeristische_verhuur import (
    get_vakantieverhuur_meldingen,
    get_vakantieverhuur_registration,
    get_vakantieverhuur_registrations_by_bag_id,
)

logger = logging.getLogger(__name__)

OPEN_CASES_QUERY_PARAMETER = "open_cases"
open_cases = OpenApiParameter(
    name=OPEN_CASES_QUERY_PARAMETER,
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Open Cases",
)


class AddressViewSet(
    ViewSet, GenericAPIView, mixins.UpdateModelMixin, PermitDetailsMixin
):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    lookup_field = "bag_id"
    http_method_names = ["get", "patch", "post"]

    def update(self, request, bag_id, *args, **kwargs):
        address_instance = Address.objects.get(bag_id=bag_id)
        serializer = self.serializer_class(
            instance=address_instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=ResidentsSerializer,
        url_path="residents",
        permission_classes=[permissions.CanAccessBRP],
    )
    @extend_schema(request={GetResidentsSerializer})
    def residents_by_bag_id(self, request, bag_id):
        # Get address
        try:
            address = Address.objects.get(bag_id=bag_id)
        except Address.DoesNotExist:
            address = Address(bag_id=bag_id)

        # If no nummeraanduiding_id, get it!
        if not address.nummeraanduiding_id:
            try:
                address.update_bag_data()
            except Exception:
                return Response(
                    {"error": "BAG data could not be obtained"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # nummeraanduiding_id should have been retrieved, so get BRP data
        if address.nummeraanduiding_id:
            obo_access_token = request.data.get("obo_access_token")
            brp_data, status_code = get_brp_by_nummeraanduiding_id(
                request, address.nummeraanduiding_id, obo_access_token
            )
            serialized_residents = ResidentsSerializer(data=brp_data)
            serialized_residents.is_valid(raise_exception=True)
            return Response(serialized_residents.data, status=status_code)

        return Response(
            {"error": "no nummeraanduiding_id found"}, status=status.HTTP_404_NOT_FOUND
        )

    @action(
        detail=True,
        methods=["get"],
        serializer_class=BrpSerializer,
        url_path="residents-new",
        permission_classes=[permissions.CanAccessBRP],
    )
    @extend_schema(
        description="Gets the residents associated with this address",
    )
    def residents_by_bag_id_new_api(self, request, bag_id):
        # Get address
        try:
            address = Address.objects.get(bag_id=bag_id)
        except Address.DoesNotExist:
            address = Address(bag_id=bag_id)

        # If no nummeraanduiding_id, get it!
        if not address.nummeraanduiding_id:
            try:
                address.update_bag_data()
            except Exception:
                return Response(
                    {"error": "BAG data could not be obtained"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # nummeraanduiding_id should have been retrieved, so get BRP data
        if address.nummeraanduiding_id:
            try:
                response = BrpRequest().get_brp_with_nummeraanduiding_id(
                    address.nummeraanduiding_id, request.user.email
                )

                serialized_residents = BrpSerializer(data=response)
                serialized_residents.is_valid(raise_exception=True)
                # return Response(serialized_residents.data, status=status_code)
                return Response(serialized_residents.data)
            except Exception as e:
                logger.error(f"Failed to fetch residents for bag id {bag_id}: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    @extend_schema(
        description="Gets all meldingen for holiday rental",
        responses={status.HTTP_200_OK: MeldingenSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Shows meldingen from the given date.",
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Shows meldingen till the given date.",
            ),
        ],
    )
    @action(
        detail=True,
        methods=["get"],
        serializer_class=MeldingenSerializer,
        url_path="meldingen",
    )
    def meldingen(self, request, bag_id):
        offset = request.GET.get("offset", 1)
        limit = request.GET.get("limit", 1000)
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        params = {
            "pageNumber": offset,
            "pageSize": limit,
        }
        if start_date:
            params["startDatum"] = start_date
        if end_date:
            params["eindDatum"] = end_date

        try:
            vakantieverhuur_meldingen_data, status_code = get_vakantieverhuur_meldingen(
                bag_id, query_params=params
            )
            serialized_meldingen = MeldingenSerializer(
                data=vakantieverhuur_meldingen_data
            )
            serialized_meldingen.is_valid(raise_exception=True)
            return Response(serialized_meldingen.data, status=status_code)
        except Exception:
            return Response(
                {"error": "Toeristische verhuur meldingen could not be obtained"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        description="Gets all registrations for holiday rental by bag_id",
        responses={status.HTTP_200_OK: RegistrationDetailsSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="registrations",
        methods=["get"],
        pagination_class=None,
    )
    def registrations(self, request, bag_id):
        try:
            (
                registrations_data,
                status_code,
            ) = get_vakantieverhuur_registrations_by_bag_id(
                bag_id,
            )
            serialized_registrations = RegistrationNumberSerializer(
                data=registrations_data, many=True
            )
            serialized_registrations.is_valid(raise_exception=True)

            # Fetch details for each registration number
            detailed_registrations = []
            for registration in serialized_registrations.data:
                # Remove spaces from registration number
                registration_number = registration["registrationNumber"].replace(
                    " ", ""
                )
                try:
                    # Fetch detailed data for the current registrationNumber
                    (
                        registration_details,
                        detail_status_code,
                    ) = get_vakantieverhuur_registration(registration_number)
                    if detail_status_code == 200:  # Only append if successful
                        detailed_registrations.append(registration_details)
                    else:
                        print(
                            f"Failed to fetch details for {registration_number}. Status: {detail_status_code}"
                        )
                except Exception as e:
                    print(f"Error fetching details for {registration_number}: {e}")

            # Sort detailed_registrations by 'createdAt' with the newest first
            detailed_registrations = sorted(
                detailed_registrations,
                key=lambda x: x.get("createdAt", ""),
                reverse=True,
            )

            serializer = RegistrationDetailsSerializer(
                detailed_registrations, many=True
            )

            return Response(serializer.data, status=status_code)
        except Exception:
            return Response(
                {"error": "Toeristische verhuur registrations could not be obtained"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
