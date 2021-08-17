from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import User


class PermissionSerializer(serializers.CharField):
    def to_representation(self, instance):
        return instance.codename


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.ListSerializer(child=PermissionSerializer())

    class Meta:
        model = Group
        exclude = [
            "id",
        ]


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False)


class UserDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False)
    groups = GroupSerializer(required=False, many=True)

    class Meta:
        model = User
        exclude = [
            "password",
            "last_login",
            "is_superuser",
            "is_staff",
            "is_active",
            "date_joined",
            "user_permissions",
        ]


class OIDCAuthenticateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
