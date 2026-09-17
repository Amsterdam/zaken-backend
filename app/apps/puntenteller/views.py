import logging

from apps.addresses.models import Address
from apps.puntenteller.models import Gebruikersinvoer
from apps.puntenteller.puntenteller import Puntenteller
from apps.puntenteller.serializers import (
    GebouwDataSerializer,
    GebruikersinvoerSerializer,
)
from apps.users.permissions import rest_permission_classes_for_top
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from utils.api_queries_puntenteller import get_energie_label, get_oppervlakte, get_woz

logger = logging.getLogger(__name__)


class AdresPuntentellerViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = GebruikersinvoerSerializer
    queryset = Gebruikersinvoer.objects.all()

    def list(self, request, *args, **kwargs):
        bag_id = kwargs.get("bag_id")
        adres = self._get_adres(bag_id)
        gebruikersinvoer_lijst = self.get_queryset().filter(adres=adres)
        response_data = [_met_punten(item) for item in gebruikersinvoer_lijst]
        return Response(response_data)

    def create(self, request, *args, **kwargs):
        bag_id = kwargs.get("bag_id")
        adres = self._get_adres(bag_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gebruikersinvoer = serializer.save(adres=adres, gebruiker=request.user)
        return Response(
            _alleen_resultaten(gebruikersinvoer), status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="invoerwaarden",
        serializer_class=GebouwDataSerializer,
    )
    def invoerwaarden(self, request, *args, **kwargs):
        bag_id = kwargs.get("bag_id")
        try:
            adres = Address.objects.get(bag_id=bag_id)
        except Address.DoesNotExist:
            adres = Address(bag_id=bag_id)

        if not adres.nummeraanduiding_id:
            try:
                adres.update_bag_data()
            except Exception:
                return Response(
                    {"detail": "Gebouwdata kon niet worden opgehaald"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        try:
            energie_data = get_energie_label(adres.bag_id)
            gebruiksoppervlakte = get_oppervlakte(adres.bag_id)
            woz_data = get_woz(adres.nummeraanduiding_id)
        except Exception as exception:
            logger.exception("Fout bij ophalen van externe gebouwdata", exception)
            return Response(
                {"detail": "Externe gebouwdata kon niet worden opgehaald"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GebouwDataSerializer(
            {
                "straat": adres.street_name,
                "huisnummer": adres.number,
                "bouwjaar": energie_data.get("bouwjaar") if energie_data else None,
                "gebruiksoppervlakte": gebruiksoppervlakte,
                "woz_waarden": woz_data.get("woz_waarden") if woz_data else None,
                "wozobjectnummer": (
                    woz_data.get("wozobjectnummer") if woz_data else None
                ),
                "energielabel": (
                    energie_data.get("energielabel") if energie_data else None
                ),
            }
        )
        return Response(serializer.data)

    def _get_adres(self, bag_id):
        adres = Address.get_or_create_by_bag_id(bag_id)
        if not adres.nummeraanduiding_id:
            adres.save()
        return adres


class PuntentellingViewSet(GenericViewSet, RetrieveModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = GebruikersinvoerSerializer
    queryset = Gebruikersinvoer.objects.all()

    def retrieve(self, request, *args, **kwargs):
        gebruikersinvoer = self.get_object()
        return Response(_met_punten(gebruikersinvoer))

    def partial_update(self, request, *args, **kwargs):
        gebruikersinvoer = self.get_object()
        serializer = self.get_serializer(
            gebruikersinvoer, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        gebruikersinvoer = serializer.save()
        return Response(_met_punten(gebruikersinvoer))


def _met_punten(gebruikersinvoer):
    response_data = GebruikersinvoerSerializer(gebruikersinvoer).data
    resultaat = Puntenteller(gebruikersinvoer).bereken_resultaat()
    response_data["punten"] = resultaat.totaal_punten_na_caps
    response_data["punten_resultaat"] = resultaat.as_dict()
    return response_data


def _alleen_resultaten(gebruikersinvoer):
    return Puntenteller(gebruikersinvoer).bereken_resultaat().as_dict()
