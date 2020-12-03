from rest_framework import serializers

from .models import SupportContact


class SupportContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportContact
        fields = "__all__"
