from rest_framework import serializers


class PushStateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    gauge_date = serializers.DateField(required=False, allow_null=True)
    invoice_identification = serializers.CharField(required=True)


class PushSerializer(serializers.Serializer):
    identification = serializers.CharField(required=True)
    case_type = serializers.CharField(required=True)
    bag_id = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False)
    states = PushStateSerializer(many=True, required=False)
