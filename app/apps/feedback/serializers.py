from rest_framework import serializers


class FeedbackSerializer(serializers.Serializer):
    feedback = serializers.CharField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    url = serializers.CharField()
    user_agent = serializers.CharField(required=False)  # Optional field for user-agent
    screen = serializers.CharField(
        required=False
    )  # Optional field for screen (viewport browser)
