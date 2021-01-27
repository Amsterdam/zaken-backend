from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.visits.models import Visit
from rest_framework import serializers


class VisitSerializer(serializers.ModelSerializer):
    authors = UserSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="authors", many=True
    )

    class Meta:
        model = Visit
        fields = "__all__"


class TopVisitSerializer(serializers.Serializer):
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
