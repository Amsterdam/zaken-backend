from apps.puntenteller.models import Gebruikersinvoer
from rest_framework import serializers


class GebouwDataSerializer(serializers.Serializer):
    straat = serializers.CharField(allow_null=True)
    huisnummer = serializers.CharField(allow_null=True)
    bouwjaar = serializers.IntegerField(allow_null=True)
    gebruiksoppervlakte = serializers.IntegerField(allow_null=True)
    woz = serializers.IntegerField(allow_null=True)
    woz_jaar = serializers.IntegerField(allow_null=True)
    wozobjectnummer = serializers.IntegerField(allow_null=True)
    energielabel = serializers.CharField(allow_null=True)


class GebruikersinvoerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gebruikersinvoer
        fields = "__all__"
        read_only_fields = ("gebruiker",)
