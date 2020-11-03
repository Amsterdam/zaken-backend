from apps.users.serializers import UserSerializer
from rest_framework import serializers

from .models import Visit


class VisitSerializer(serializers.ModelSerializer):
    authors = UserSerializer(many=True)

    class Meta:
        model = Visit
        fields = "__all__"


class AddVisitSerializer(serializers.Serializer):
    case_identification = serializers.CharField()
    start_time = serializers.CharField()
    observations = serializers.ListField(child=serializers.CharField(max_length=255))
    situation = serializers.CharField()
    authors = serializers.ListField(child=serializers.CharField(max_length=255))
    can_next_visit_go_ahead = serializers.BooleanField(allow_null=True)
    can_next_visit_go_ahead_description = serializers.CharField(allow_null=True)
    suggest_next_visit = serializers.CharField(allow_null=True)
    suggest_next_visit_description = serializers.CharField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
