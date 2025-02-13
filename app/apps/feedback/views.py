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
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":rocket: Nieuwe feedback ontvangen! ",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Applicatie:*\n:house: AZA"},
                        {"type": "mrkdwn", "text": f"*E-mail:*\n {data['user'].email}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*URL:*\n <{data['url']}>"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":loudspeaker: *Feedback: *\n ```{data['feedback']}```",
                    },
                },
                {"type": "divider"},
            ]
        }
