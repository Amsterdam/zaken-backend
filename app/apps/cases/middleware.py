import re

from django.http import JsonResponse
from rest_framework import status

from .models import Case


class SensitiveCaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Controleer beide endpoints
        pattern = r"^/api/v1/(cases|data/cases)/(\d+)/"
        match = re.match(pattern, request.path)
        if match:
            case_id = match.group(2)
            case = Case.objects.filter(pk=case_id).first()
            if (
                case
                and case.sensitive
                and request.user.is_authenticated
                and not request.user.has_perm("users.access_sensitive_dossiers")
            ):
                return JsonResponse(
                    {"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN
                )

        return response
