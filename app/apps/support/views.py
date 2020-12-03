from rest_framework import generics
from rest_framework.viewsets import ViewSet

from .models import SupportContact
from .serializers import SupportContactSerializer


class SupportContactView(generics.ListAPIView, ViewSet):
    queryset = SupportContact.objects.all()
    serializer_class = SupportContactSerializer
