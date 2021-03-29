from apps.cases.models import CaseTeam
from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from rest_framework import serializers


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ["id", "name"]


class WeekSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekSegment
        fields = ["id", "name"]


class DaySegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaySegment
        fields = ["id", "name"]


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ["id", "name", "weight"]


class ScheduleSerializer(serializers.ModelSerializer):
    action = ActionSerializer(required=True)
    week_segment = WeekSegmentSerializer(required=True)
    day_segment = DaySegmentSerializer(required=True)
    priority = PrioritySerializer(required=True)

    class Meta:
        model = Schedule
        fields = "__all__"


class ScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = (
            "action",
            "week_segment",
            "day_segment",
            "priority",
            "case",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        action = validated_data.pop("action")
        case = validated_data.pop("case")
        schedule, _ = Schedule.objects.update_or_create(
            action=action, case=case, defaults=validated_data
        )
        return schedule


class TeamScheduleTypesSerializer(serializers.ModelSerializer):
    actions = ActionSerializer(many=True)
    week_segments = WeekSegmentSerializer(many=True)
    day_segments = DaySegmentSerializer(many=True)
    priorities = PrioritySerializer(many=True)

    class Meta:
        model = CaseTeam
        fields = ["actions", "week_segments", "day_segments", "priorities"]
