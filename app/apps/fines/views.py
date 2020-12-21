from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.fines.serializers import FineListSerializer
from apps.fines.api_queries_belastingen import get_fines

class FinesViewSet(ViewSet):
    @extend_schema(
        parameters=[id],
        description="Get permit checkmarks based on bag id",
        responses={200: FineListSerializer()},
    )
    def retrieve(self, request, pk):
        try:
            fines = get_fines(pk)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FineListSerializer(data=fines)

        if serializer.is_valid():
            return Response(serializer.data)
    
        return Response(serializer.initial_data)

