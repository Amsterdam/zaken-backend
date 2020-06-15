from rest_framework import serializers


class StateTypeSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    statustekst = serializers.CharField(required=True)
    omschrijving = serializers.CharField(required=True)
    uuid = serializers.CharField(read_only=True)
    zaaktype = serializers.CharField(required=True)
    volgnummer = serializers.IntegerField(required=True, max_value=9999, min_value=1)
