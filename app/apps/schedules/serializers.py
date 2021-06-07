from apps.cases.models import CaseTheme
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
            "description",
            "case",
            "camunda_task_id",
        )
        read_only_fields = ("id",)


class ThemeScheduleTypesSerializer(serializers.ModelSerializer):
    actions = ActionSerializer(many=True)
    week_segments = WeekSegmentSerializer(many=True)
    day_segments = DaySegmentSerializer(many=True)
    priorities = PrioritySerializer(many=True)

    class Meta:
        model = CaseTheme
        fields = ["actions", "week_segments", "day_segments", "priorities"]
