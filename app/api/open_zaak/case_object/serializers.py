from rest_framework import serializers


class CaseObjectSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    zaakUuid = serializers.CharField(read_only=True)
    zaak = serializers.URLField(required=True)
    object = serializers.URLField(required=True)
    objectType = serializers.CharField(required=True)
