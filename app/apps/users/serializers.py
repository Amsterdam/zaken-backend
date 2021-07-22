from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from .models import User


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"

    def to_representation(self, instance):
        return instance.codename


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(required=False, many=True)
    # permissions = serializers.ListSerializer(child=serializers.CharField(source="codename"))

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
