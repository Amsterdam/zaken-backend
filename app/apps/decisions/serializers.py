from apps.addresses.serializers import AddressSerializer
from apps.cases.serializers import CaseThemeSerializer
from apps.decisions.models import Decision, DecisionType
from rest_framework import serializers


class DecisionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionType
        fields = "__all__"


class DecisionTypeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionType
        fields = [
            "id",
            "name",
        ]


class DecisionSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def create(self, validated_data):
        """
        Create a decision with a unique sanction_id if the decision-type is sanction.
        """

        # First create the Decision so we have an 'id'
        decision = super().create(validated_data)

        if decision.decision_type.is_sanction:
            # If the decision is a sanction generate our unique sanction_id
            # and save the object again
            decision.sanction_id = f"AZA{decision.case.id}-{decision.id}"
            decision.save()

        return decision

    class Meta:
        model = Decision
        exclude = ["summon"]
        read_only_fields = ["sanction_id"]


class DecisionSanctionSerializer(serializers.ModelSerializer):
    address = AddressSerializer(source="case.address", read_only=True)
    theme = CaseThemeSerializer(source="case.theme", read_only=True)
    decision_type = DecisionTypeNameSerializer(read_only=True)

    class Meta:
        model = Decision
        exclude = [
            "case",
            "author",
            "summon",
            "description",
            "camunda_task_id",
        ]
