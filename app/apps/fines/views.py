from apps.fines.api_queries_belastingen import get_fines
from apps.fines.serializers import FineListSerializer
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class FinesViewSet(ViewSet):
    queryset = []  # Add this line to set an empty queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(name="id", description="Bag ID", required=True, type=int)
        ],
        description="Get permit checkmarks based on bag id",
        responses={200: FineListSerializer()},
    )
    def retrieve(self, request, pk):
        try:
            fines = get_fines(pk)
        except Exception:
            return Response(
                {"error": "Onverwachte fout bij het ophalen van boetes"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FineListSerializer(data=fines)

        if serializer.is_valid():
            return Response(serializer.data)

        return Response(serializer.initial_data)
