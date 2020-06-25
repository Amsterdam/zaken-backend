from rest_framework import serializers

class PushSerializer(serializers.Serializer):
    case_id = serializers.CharField(required=True)