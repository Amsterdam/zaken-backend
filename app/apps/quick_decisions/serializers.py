from apps.quick_decisions.models import QuickDecision, QuickDecisionType
from rest_framework import serializers


class QuickDecisionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickDecisionType
        fields = "__all__"


class QuickDecisionSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = QuickDecision
        exclude = ["summon"]
