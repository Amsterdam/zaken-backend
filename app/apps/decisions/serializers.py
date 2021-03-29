from apps.decisions.models import Decision, DecisionType
from rest_framework import serializers


class DecisionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionType
        fields = "__all__"


class DecisionSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Decision
        exclude = ["summon"]
