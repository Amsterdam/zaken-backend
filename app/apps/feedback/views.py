import json

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializers import FeedbackSerializer


class FeedbackViewset(GenericAPIView):
    serializer_class = FeedbackSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        body = self._create_slack_message_body(data)
        response = requests.post(
            settings.SLACK_WEBHOOK_URL,
            data=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return Response(status=status.HTTP_200_OK)

    def _create_slack_message_body(self, data):
        return {
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": ":house:  AZA"}},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":earth_africa:  <{data['url']}>",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f":woman-tipping-hand::skin-tone-5:  {data['user'].email}",
                        }
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":loudspeaker:  {data['feedback']}",
                    },
                },
            ]
        }
