from rest_framework import serializers


class PushSerializer(serializers.Serializer):
    identificatie = serializers.CharField(required=True)
    omschrijving = serializers.CharField(required=True)
    toelichting = serializers.CharField(required=True)
    startdatum = serializers.DateField(required=True)
    einddatum = serializers.DateField(required=False)


class PushCheckActionSerializer(serializers.Serializer):
    identificatie = serializers.CharField(required=True)
    check_actie = serializers.BooleanField(required=True)
