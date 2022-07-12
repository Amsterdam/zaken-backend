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
        fields = ("id", "name", "weight")


class PriorityTinySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ("weight",)


class ScheduleDataSerializer(serializers.ModelSerializer):
    action = ActionSerializer(required=True)
    week_segment = WeekSegmentSerializer(required=True)
    day_segment = DaySegmentSerializer(required=True)
    priority = PriorityTinySerializer(required=True)

    class Meta:
        model = Schedule
        fields = "__all__"


class ScheduleSerializer(serializers.ModelSerializer):
    priority = PriorityTinySerializer(required=True)

    class Meta:
        model = Schedule
        exclude = (
            "action",
            "author",
            "case",
            "case_user_task_id",
            "date_added",
            "date_modified",
            "day_segment",
            "description",
            "housing_corporation_combiteam",
            "id",
            "visit_from_datetime",
            "week_segment",
        )


class ScheduleCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Schedule
        fields = (
            "author",
            "action",
            "week_segment",
            "day_segment",
            "priority",
            "description",
            "case",
            "case_user_task_id",
            "visit_from_datetime",
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
