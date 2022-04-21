import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification


class ReceiveNotificationView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        Notification.objects.create(data=json.dumps(request.data))
        return Response({}, status=status.HTTP_201_CREATED)
