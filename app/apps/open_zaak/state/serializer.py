from rest_framework import serializers


class OpenZaakStateSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    datumStatusGezet = serializers.DateField(read_only=True)
    zaak = serializers.URLField(required=True)
    statustype = serializers.URLField(required=True)
    statustoelichting = serializers.CharField(required=False)
