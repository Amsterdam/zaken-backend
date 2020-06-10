from rest_framework import serializers

class CaseSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    identificatie = serializers.CharField(read_only=True)
    omschrijving = serializers.CharField(read_only=True)
    startdatum = serializers.DateField(read_only=True)
    einddatum = serializers.DateField(read_only=True)
    status = serializers.URLField(read_only=True)