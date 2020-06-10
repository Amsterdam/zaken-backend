from rest_framework import serializers

class StateTypeSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    statustekst = serializers.CharField(read_only=True)
    uuid = serializers.CharField(read_only=True)

class CaseObjectSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    zaak = serializers.URLField(read_only=True)
    zaakUuid = serializers.CharField(read_only=True)
    object = serializers.URLField(read_only=True)
    objectType = serializers.CharField(read_only=True)

class CaseTypeSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    omschrijving = serializers.CharField(read_only=True)
    doel = serializers.CharField(read_only=True)
    aanleiding = serializers.CharField(read_only=True)
    onderwerp = serializers.CharField(read_only=True)

class CaseSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    identificatie = serializers.CharField(read_only=True)
    omschrijving = serializers.CharField(read_only=True)
    startdatum = serializers.DateField(read_only=True)
    einddatum = serializers.DateField(read_only=True)
    status = serializers.URLField(read_only=True)

class CatalogSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)

class StateSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)