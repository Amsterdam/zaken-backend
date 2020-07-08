from apps.open_zaak.catalog.serializers import CatalogSerializer
from apps.open_zaak.catalog.wrappers import Catalog
from apps.open_zaak.view_helpers import list_helper, retrieve_helper
from rest_framework import viewsets


class CatalogViewSet(viewsets.ViewSet):
    serializer_class = CatalogSerializer
    data_wrapper = Catalog
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)
