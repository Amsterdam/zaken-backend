from apps.cases.models import Address, Case, Project
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = [
            "id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
        ]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ["id"]


class CaseSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(required=True)
    address = AddressSerializer(required=True)

    class Meta:
        model = Case
        fields = "__all__"

    def create(self, validated_data):
        print("=-=-=-=-")
        print("Valid data", validated_data)

        project_data = validated_data.pop("project")
        print("Project data", project_data)
        project = Project.get(project_data.get("name"))

        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(**validated_data, project=project, address=address)

        return case
