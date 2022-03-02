from apps.cases.models import Case
from apps.summons.models import Summon, SummonedPerson, SummonType
from rest_framework import serializers


class SummonedPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummonedPerson
        fields = (
            "id",
            "first_name",
            "preposition",
            "last_name",
            "person_role",
            "summon",
            "entity_name",
            "function",
        )
        read_only_fields = ("summon",)


class SummonSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    type = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=SummonType.objects.all()
    )
    type_name = serializers.CharField(source="type.name", read_only=True)
    case = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=Case.objects.all()
    )
    persons = SummonedPersonSerializer(required=True, many=True)

    class Meta:
        model = Summon
        fields = "__all__"

    def create(self, validated_data):
        persons = validated_data.pop("persons")
        summon = Summon.objects.create(**validated_data)

        for person in persons:
            SummonedPerson.objects.create(summon=summon, **person)

        summon.complete_task()
        return summon


class SummonTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummonType
        fields = (
            "id",
            "name",
            "workflow_option",
        )
