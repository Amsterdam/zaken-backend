from rest_framework import serializers

class PushSerializer(serializers.Serializer):
    identificatie = serializers.CharField(required=True)
    omschrijving = serializers.CharField(required=True)
    toelichting = serializers.CharField(required=True)