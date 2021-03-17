from apps.decisions.models import Decision, DecisionType
from rest_framework import serializers


class DecisionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionType
        fields = "__all__"


class DecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Decision
        fields = ["case", "decision_type", "description"]
