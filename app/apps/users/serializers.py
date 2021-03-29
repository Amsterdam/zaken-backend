from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False)


class OIDCAuthenticateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
