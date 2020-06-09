from rest_framework import serializers

class StateTypeSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    statustekst = serializers.CharField(read_only=True)
    pk = serializers.CharField(read_only=True)