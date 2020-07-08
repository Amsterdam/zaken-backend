from rest_framework import serializers


class CaseTypeSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    omschrijving = serializers.CharField(read_only=True)
    doel = serializers.CharField(read_only=True)
    aanleiding = serializers.CharField(read_only=True)
    onderwerp = serializers.CharField(read_only=True)
