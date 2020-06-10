from rest_framework import serializers

class CaseObjectSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    zaak = serializers.URLField(read_only=True)
    zaakUuid = serializers.CharField(read_only=True)
    object = serializers.URLField(read_only=True)
    objectType = serializers.CharField(read_only=True)