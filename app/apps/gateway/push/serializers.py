from rest_framework import serializers


class PushSerializer(serializers.Serializer):
    identification = serializers.CharField(required=True)
    case_type = serializers.CharField(required=True)
    bag_id = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False)


class PushCheckActionSerializer(serializers.Serializer):
    identification = serializers.CharField(required=True)
    check_action = serializers.BooleanField(required=True)
