import logging

from apps.addresses.models import Address
from apps.puntenteller.models import Gebruikersinvoer
from apps.puntenteller.puntenteller import Puntenteller
from apps.puntenteller.serializers import (
    GebouwDataSerializer,
    GebruikersinvoerRequestSerializer,
    GebruikersinvoerResponseSerializer,
    GebruikersinvoerSerializer,
)
from apps.users.permissions import rest_permission_classes_for_top
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from utils.api_queries_puntenteller import get_energie_label, get_oppervlakte, get_woz

logger = logging.getLogger(__name__)


class AdresPuntentellerViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = GebruikersinvoerSerializer
    queryset = Gebruikersinvoer.objects.all()

    def get_queryset(self):
        # Filter on the bag_id directly, so a GET doesn't create the address.
        return (
            super()
            .get_queryset()
            .filter(adres__bag_id=self.kwargs["bag_id"])
            .select_related("author")
        )

    @extend_schema(responses=GebruikersinvoerResponseSerializer(many=True))
    def list(self, request, *args, **kwargs):
        return Response([_met_punten(item) for item in self.get_queryset()])

    @extend_schema(
        request=GebruikersinvoerRequestSerializer,
        responses={status.HTTP_201_CREATED: GebruikersinvoerResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        bag_id = kwargs.get("bag_id")
        adres = self._get_adres(bag_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gebruikersinvoer = serializer.save(adres=adres, author=request.user)
        return Response(_met_punten(gebruikersinvoer), status=status.HTTP_201_CREATED)

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
            logger.exception("Fout bij ophalen van externe gebouwdata: %s", exception)
            return Response(
                {"detail": "Externe gebouwdata kon niet worden opgehaald"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GebouwDataSerializer(
            {
                "straat": adres.street_name,
                "huisnummer": adres.number,
                "gebruiksoppervlakte": gebruiksoppervlakte,
                "woz_waarden": woz_data.get("woz_waarden") if woz_data else None,
                "wozobjectnummer": (
                    woz_data.get("wozobjectnummer") if woz_data else None
                ),
                "energie": {
                    "bouwjaar": energie_data.get("bouwjaar") if energie_data else None,
                    "energielabel": (
                        energie_data.get("energielabel") if energie_data else None
                    ),
                    "energieindex": (
                        energie_data.get("energieindex") if energie_data else None
                    ),
                    "registratiedatum": (
                        energie_data.get("registratiedatum") if energie_data else None
                    ),
                    "opnamedatum": (
                        energie_data.get("opnamedatum") if energie_data else None
                    ),
                    "meting_geldig_tot": (
                        energie_data.get("meting_geldig_tot") if energie_data else None
                    ),
                },
            }
        )
        return Response(serializer.data)

    def _get_adres(self, bag_id):
        adres = Address.get_or_create_by_bag_id(bag_id)
        if not adres.nummeraanduiding_id:
            adres.save()
        return adres


class PuntentellingViewSet(GenericViewSet, RetrieveModelMixin, DestroyModelMixin):
    """
    A saved puntentelling. `completed` only shows whether the author is done with it;
    it can still be changed and deleted either way.
    """

    permission_classes = rest_permission_classes_for_top()
    serializer_class = GebruikersinvoerSerializer
    queryset = Gebruikersinvoer.objects.select_related("author")

    @extend_schema(responses=GebruikersinvoerResponseSerializer)
    def retrieve(self, request, *args, **kwargs):
        gebruikersinvoer = self.get_object()
        return Response(_met_punten(gebruikersinvoer))

    @extend_schema(
        request=GebruikersinvoerRequestSerializer,
        responses=GebruikersinvoerResponseSerializer,
    )
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
    response_data["punten"] = float(resultaat.totaal_punten)
    response_data["punten_resultaat"] = resultaat.as_dict()
    return response_data
