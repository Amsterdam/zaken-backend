from apps.decisions.models import Decision, DecisionType
from rest_framework import serializers


class DecisionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionType
        fields = "__all__"


class DecisionSerializer(serializers.ModelSerializer):
    # decision_type_full = DecisionTypeSerializer(read_only=True)
    # decision_type = serializers.PrimaryKeyRelatedField(
    #     write_only=True, queryset=DecisionType.objects.all()
    # )

    class Meta:
        model = Decision
        fields = "__all__"
