import re

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status

from .models import Case


class SensitiveCaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        match = re.match(r"^/api/v1/cases/(\d+)/", request.path)
        if request.path.startswith("/api/v1/cases/") and match:
            case_id = match.group(1)
            case = get_object_or_404(Case, pk=case_id)
            if (
                case.sensitive
                and request.user.is_authenticated
                and not request.user.has_perm("users.access_sensitive_dossiers")
            ):
                return JsonResponse(
                    {"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN
                )

        return response
