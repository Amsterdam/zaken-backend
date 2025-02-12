from rest_framework import serializers


class FeedbackSerializer(serializers.Serializer):
    feedback = serializers.CharField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    url = serializers.CharField()
