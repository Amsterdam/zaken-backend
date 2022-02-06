from collections import OrderedDict

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class EmptyPagination(PageNumberPagination):
    count = None

    def paginate_queryset(self, queryset, request, view=None):
        """Checking NotFound exception"""
        self.count = queryset.count()
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:  # intercept NotFound exception
            return list()

    def get_paginated_response(self, data):
        """Avoid case when self does not have page properties for empty list"""
        if hasattr(self, "page") and self.page is not None:
            return super().get_paginated_response(data)
        else:
            return Response(
                OrderedDict(
                    [
                        ("count", self.count),
                        ("next", None),
                        ("previous", None),
                        ("results", data),
                    ]
                )
            )
