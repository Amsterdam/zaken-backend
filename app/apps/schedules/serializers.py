from apps.schedules.models import (
    DaySegment,
    Priority,
    Schedule,
    ScheduleType,
    WeekSegment,
)
from rest_framework import serializers


class ScheduleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleType
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
    schedule_type = ScheduleTypeSerializer(required=True)
    week_segment = WeekSegmentSerializer(required=True)
    day_segment = DaySegmentSerializer(required=True)
    priority = PrioritySerializer(required=True)

    class Meta:
        model = Schedule
        fiels = "__all__"
